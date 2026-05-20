"""Fixtures — upcoming and recent matches, with top-line predictions."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.schemas import MatchSummary
from app.db import get_db
from app.db.models import Match, Prediction

router = APIRouter()


@router.get("", response_model=list[MatchSummary])
async def list_fixtures(
    db: AsyncSession = Depends(get_db),
    days_ahead: int = Query(14, ge=1, le=60),
    days_back: int = Query(7, ge=0, le=60),
) -> list[MatchSummary]:
    """Return matches in a window, ordered by kickoff."""
    now = datetime.now(UTC)
    from_dt = now - timedelta(days=days_back)
    to_dt = now + timedelta(days=days_ahead)

    stmt = (
        select(Match)
        .where(Match.kickoff >= from_dt, Match.kickoff <= to_dt)
        .order_by(Match.kickoff.asc())
        .options(
            selectinload(Match.home_team),
            selectinload(Match.away_team),
            selectinload(Match.competition),
            selectinload(Match.predictions),
        )
    )

    result = await db.execute(stmt)
    matches = result.scalars().all()

    rows: list[MatchSummary] = []
    for m in matches:
        # Pick the ensemble prediction if present, else first available
        pred = _pick_prediction(m.predictions)
        rows.append(
            MatchSummary(
                id=m.id,
                kickoff=m.kickoff,
                matchday=m.matchday,
                status=m.status,
                home_team=m.home_team,  # type: ignore[arg-type]
                away_team=m.away_team,  # type: ignore[arg-type]
                competition=m.competition,  # type: ignore[arg-type]
                home_score=m.home_score,
                away_score=m.away_score,
                prob_home=pred.prob_home if pred else None,
                prob_draw=pred.prob_draw if pred else None,
                prob_away=pred.prob_away if pred else None,
            )
        )
    return rows


def _pick_prediction(predictions: list[Prediction]) -> Prediction | None:
    if not predictions:
        return None
    # Prefer ensemble, then dixon_coles, else first
    by_name = {p.model_name: p for p in predictions}
    for preferred in ("ensemble", "dixon_coles", "xgboost", "bayesian"):
        if preferred in by_name:
            return by_name[preferred]
    return predictions[0]
