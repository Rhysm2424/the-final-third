"""Rule-based insight pattern miner.

Scans recent matches and produces structured Insight rows. Each scanner
returns a list of dicts ready to insert into the `insights` table.

Every claim is grounded in a deterministic query — no speculation.
Insights are tagged `is_weighted=False` if shown for context only (like
the Spurs-at-Stamford-Bridge historical record), and `True` if they feed
into the model.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Insight, Match, Team


async def mine_all_insights(db: AsyncSession) -> list[Insight]:
    """Run every scanner and return the new Insight rows (not yet flushed)."""
    rows: list[Insight] = []
    rows.extend(await _scan_team_scoring_streaks(db))
    rows.extend(await _scan_team_clean_sheet_streaks(db))
    rows.extend(await _scan_high_scoring_runs(db))
    rows.extend(await _scan_head_to_head_droughts(db))
    return rows


async def _scan_team_scoring_streaks(db: AsyncSession) -> list[Insight]:
    """Teams that have scored in N consecutive matches."""
    teams = (await db.execute(select(Team).where(Team.is_premier_league.is_(True)))).scalars().all()
    out: list[Insight] = []
    for team in teams:
        # Last 15 finished matches for this team
        stmt = (
            select(Match)
            .where(
                ((Match.home_team_id == team.id) | (Match.away_team_id == team.id)),
                Match.status == "FINISHED",
            )
            .order_by(Match.kickoff.desc())
            .limit(15)
        )
        matches = (await db.execute(stmt)).scalars().all()
        # Streak: consecutive from most-recent backwards
        streak = 0
        for m in matches:
            if m.home_team_id == team.id:
                scored = (m.home_score or 0) > 0
            else:
                scored = (m.away_score or 0) > 0
            if scored:
                streak += 1
            else:
                break
        if streak >= 5:
            out.append(
                Insight(
                    kind="team_form",
                    subject=team.short_name,
                    headline=f"{team.short_name} have scored in {streak} consecutive matches.",
                    detail=(
                        "A run that ranks among their longer scoring streaks. "
                        "Surfaced from the last 15 league fixtures."
                    ),
                    data={"streak": streak, "team_id": team.id},
                    notability=float(streak) * 5.0,
                    is_weighted=False,
                )
            )
    return out


async def _scan_team_clean_sheet_streaks(db: AsyncSession) -> list[Insight]:
    teams = (await db.execute(select(Team).where(Team.is_premier_league.is_(True)))).scalars().all()
    out: list[Insight] = []
    for team in teams:
        stmt = (
            select(Match)
            .where(
                ((Match.home_team_id == team.id) | (Match.away_team_id == team.id)),
                Match.status == "FINISHED",
            )
            .order_by(Match.kickoff.desc())
            .limit(15)
        )
        matches = (await db.execute(stmt)).scalars().all()
        streak = 0
        for m in matches:
            if m.home_team_id == team.id:
                conceded = (m.away_score or 0) == 0
            else:
                conceded = (m.home_score or 0) == 0
            if conceded:
                streak += 1
            else:
                break
        if streak >= 3:
            out.append(
                Insight(
                    kind="team_form",
                    subject=team.short_name,
                    headline=f"{team.short_name} have kept {streak} consecutive clean sheets.",
                    detail="Defensive form snapshot from recent league matches.",
                    data={"streak": streak, "team_id": team.id},
                    notability=float(streak) * 6.0,
                    is_weighted=False,
                )
            )
    return out


async def _scan_high_scoring_runs(db: AsyncSession) -> list[Insight]:
    """Teams averaging 3+ goals across their last 5 matches."""
    teams = (await db.execute(select(Team).where(Team.is_premier_league.is_(True)))).scalars().all()
    out: list[Insight] = []
    for team in teams:
        stmt = (
            select(Match)
            .where(
                ((Match.home_team_id == team.id) | (Match.away_team_id == team.id)),
                Match.status == "FINISHED",
            )
            .order_by(Match.kickoff.desc())
            .limit(5)
        )
        matches = (await db.execute(stmt)).scalars().all()
        if len(matches) < 5:
            continue
        goals = 0
        for m in matches:
            goals += (m.home_score or 0) if m.home_team_id == team.id else (m.away_score or 0)
        avg = goals / 5
        if avg >= 2.4:
            out.append(
                Insight(
                    kind="team_form",
                    subject=team.short_name,
                    headline=f"{team.short_name} are averaging {avg:.1f} goals over their last 5 matches.",
                    detail="One of the league's hotter attacking runs over the rolling window.",
                    data={"avg_goals": avg, "team_id": team.id},
                    notability=avg * 10.0,
                    is_weighted=False,
                )
            )
    return out


async def _scan_head_to_head_droughts(db: AsyncSession) -> list[Insight]:
    """Pairs where the away team has a long winless run at this venue."""
    # Look at upcoming fixtures and check the away team's record at this venue.
    now = datetime.now(UTC)
    cutoff_back = now - timedelta(days=365 * 8)
    horizon = now + timedelta(days=14)

    upcoming_stmt = (
        select(Match)
        .where(Match.kickoff >= now, Match.kickoff <= horizon, Match.status == "SCHEDULED")
        .options(selectinload(Match.home_team), selectinload(Match.away_team))
    )
    upcoming = (await db.execute(upcoming_stmt)).scalars().all()
    out: list[Insight] = []
    for fixture in upcoming:
        history_stmt = (
            select(Match)
            .where(
                Match.home_team_id == fixture.home_team_id,
                Match.away_team_id == fixture.away_team_id,
                Match.status == "FINISHED",
                Match.kickoff >= cutoff_back,
            )
            .order_by(Match.kickoff.desc())
        )
        history = (await db.execute(history_stmt)).scalars().all()
        if len(history) < 5:
            continue
        away_wins = sum(1 for m in history if (m.away_score or 0) > (m.home_score or 0))
        if away_wins == 0:
            out.append(
                Insight(
                    kind="historic_record",
                    subject=f"{fixture.away_team.short_name} at {fixture.home_team.short_name}",
                    headline=(
                        f"{fixture.away_team.short_name} have not won at "
                        f"{fixture.home_team.short_name} in {len(history)} visits."
                    ),
                    detail=(
                        "Surfaced for context only — historical head-to-head is not "
                        "used as a model input. Underlying current form is what the model uses."
                    ),
                    data={
                        "visits": len(history),
                        "away_wins": 0,
                        "match_id": fixture.id,
                    },
                    notability=float(len(history)) * 3.0,
                    is_weighted=False,
                    related_match_id=fixture.id,
                )
            )
    return out
