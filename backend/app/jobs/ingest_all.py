"""Live ingestion job.

Pulls upcoming Premier League fixtures and recent results from
football-data.org into the local DB. Designed to be run twice daily
via Railway cron. In demo mode this script exits immediately — use
`make ingest` to force-run.

Usage:
    python -m app.jobs.ingest_all
"""

from __future__ import annotations

import asyncio
import sys
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.db import AsyncSessionLocal
from app.db.models import Competition, Match, Team
from app.ingestion import FootballDataOrgClient

PREMIER_LEAGUE_CODE = "PL"
COMPETITIONS_TO_FETCH = ["PL", "CL", "EC"]  # PL, Champions League, Euro Cups


async def run() -> int:
    configure_logging()
    log = get_logger(__name__)
    settings = get_settings()

    if settings.demo_mode:
        log.info("ingest.skip_demo_mode")
        return 0

    if not settings.football_data_api_key:
        log.error("ingest.no_api_key")
        return 1

    async with FootballDataOrgClient(settings.football_data_api_key) as client:
        async with AsyncSessionLocal() as db:
            for code in COMPETITIONS_TO_FETCH:
                try:
                    await _ingest_competition(db, client, code, log)
                except Exception as e:
                    log.exception("ingest.competition_failed", code=code, error=str(e))
                    continue
            await db.commit()

    log.info("ingest.done")
    return 0


async def _ingest_competition(
    db: AsyncSession,
    client: FootballDataOrgClient,
    code: str,
    log,
) -> None:
    log.info("ingest.competition_start", code=code)

    # Upsert competition
    comp_data = await client.get_competition(code)
    comp = await _upsert_competition(db, code, comp_data.get("name", code))

    # Upsert teams
    teams_data = await client.get_competition_teams(code)
    team_map: dict[int, Team] = {}
    for t in teams_data.get("teams", []):
        team_obj = await _upsert_team(db, t, is_premier_league=(code == PREMIER_LEAGUE_CODE))
        team_map[t["id"]] = team_obj

    # Matches in a -30d / +60d window
    now = datetime.now(UTC)
    from_str = (now - timedelta(days=30)).date().isoformat()
    to_str = (now + timedelta(days=60)).date().isoformat()
    matches_data = await client.get_competition_matches(code, date_from=from_str, date_to=to_str)

    for m in matches_data.get("matches", []):
        await _upsert_match(db, m, comp.id, team_map)

    log.info(
        "ingest.competition_done",
        code=code,
        n_teams=len(team_map),
        n_matches=len(matches_data.get("matches", [])),
    )


async def _upsert_competition(db: AsyncSession, code: str, name: str) -> Competition:
    stmt = select(Competition).where(Competition.code == code)
    existing = (await db.execute(stmt)).scalar_one_or_none()
    tier = "LEAGUE" if code == "PL" else "EUROPEAN" if code in {"CL", "EL", "EC", "ECL"} else "CUP"
    if existing:
        existing.name = name
        return existing
    comp = Competition(code=code, name=name, tier=tier)
    db.add(comp)
    await db.flush()
    return comp


async def _upsert_team(db: AsyncSession, t: dict, *, is_premier_league: bool) -> Team:
    short_name = t.get("shortName") or t.get("name") or "Unknown"
    stmt = select(Team).where(Team.short_name == short_name)
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        if is_premier_league:
            existing.is_premier_league = True
        return existing
    team = Team(
        short_name=short_name,
        full_name=t.get("name") or short_name,
        tla=t.get("tla"),
        crest_url=t.get("crest"),
        primary_color=None,
        secondary_color=None,
        is_premier_league=is_premier_league,
    )
    db.add(team)
    await db.flush()
    return team


async def _upsert_match(
    db: AsyncSession,
    m: dict,
    competition_id: int,
    team_map: dict[int, Team],
) -> None:
    external_id = str(m.get("id"))
    home_id = m.get("homeTeam", {}).get("id")
    away_id = m.get("awayTeam", {}).get("id")
    if home_id is None or away_id is None:
        return
    home_team = team_map.get(home_id)
    away_team = team_map.get(away_id)
    if home_team is None or away_team is None:
        return

    kickoff = datetime.fromisoformat(m["utcDate"].replace("Z", "+00:00"))
    score = m.get("score", {}).get("fullTime", {})
    status_map = {
        "SCHEDULED": "SCHEDULED",
        "TIMED": "SCHEDULED",
        "IN_PLAY": "LIVE",
        "PAUSED": "LIVE",
        "FINISHED": "FINISHED",
        "POSTPONED": "POSTPONED",
        "CANCELLED": "CANCELLED",
        "AWARDED": "FINISHED",
    }
    status = status_map.get(m.get("status", ""), "SCHEDULED")

    stmt = select(Match).where(Match.external_id == external_id)
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        existing.status = status
        existing.kickoff = kickoff
        existing.home_score = score.get("home")
        existing.away_score = score.get("away")
        existing.matchday = m.get("matchday")
        existing.venue = m.get("venue")
        return

    match = Match(
        external_id=external_id,
        competition_id=competition_id,
        home_team_id=home_team.id,
        away_team_id=away_team.id,
        kickoff=kickoff,
        matchday=m.get("matchday"),
        venue=m.get("venue"),
        status=status,
        home_score=score.get("home"),
        away_score=score.get("away"),
    )
    db.add(match)


if __name__ == "__main__":
    sys.exit(asyncio.run(run()))
