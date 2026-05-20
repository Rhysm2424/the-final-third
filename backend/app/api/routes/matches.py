"""Single match detail with full prediction payload."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.schemas import Driver, MatchDetail, PredictionOut, ScorelineProb
from app.db import get_db
from app.db.models import Match, Prediction

router = APIRouter()


@router.get("/{match_id}", response_model=MatchDetail)
async def get_match(match_id: int, db: AsyncSession = Depends(get_db)) -> MatchDetail:
    stmt = (
        select(Match)
        .where(Match.id == match_id)
        .options(
            selectinload(Match.home_team),
            selectinload(Match.away_team),
            selectinload(Match.competition),
            selectinload(Match.predictions),
        )
    )
    result = await db.execute(stmt)
    match = result.scalar_one_or_none()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    prediction = _pick_prediction(match.predictions)

    return MatchDetail(
        id=match.id,
        kickoff=match.kickoff,
        matchday=match.matchday,
        venue=match.venue,
        status=match.status,
        home_team=match.home_team,  # type: ignore[arg-type]
        away_team=match.away_team,  # type: ignore[arg-type]
        competition=match.competition,  # type: ignore[arg-type]
        home_score=match.home_score,
        away_score=match.away_score,
        home_xg=match.home_xg,
        away_xg=match.away_xg,
        odds_home=match.odds_home,
        odds_draw=match.odds_draw,
        odds_away=match.odds_away,
        prediction=_serialize_prediction(prediction) if prediction else None,
    )


def _pick_prediction(predictions: list[Prediction]) -> Prediction | None:
    if not predictions:
        return None
    by_name = {p.model_name: p for p in predictions}
    for preferred in ("ensemble", "dixon_coles", "xgboost", "bayesian"):
        if preferred in by_name:
            return by_name[preferred]
    return predictions[0]


def _serialize_prediction(p: Prediction) -> PredictionOut:
    scorelines = (
        [ScorelineProb(**s) for s in p.scoreline_distribution] if p.scoreline_distribution else None
    )
    drivers = [Driver(**d) for d in p.drivers] if p.drivers else None
    return PredictionOut(
        id=p.id,
        model_name=p.model_name,
        prob_home=p.prob_home,
        prob_draw=p.prob_draw,
        prob_away=p.prob_away,
        home_xg=p.home_xg,
        away_xg=p.away_xg,
        prob_btts=p.prob_btts,
        prob_over_2_5=p.prob_over_2_5,
        scoreline_distribution=scorelines,
        drivers=drivers,
        narrative=p.narrative,
        created_at=p.created_at,
    )
