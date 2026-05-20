"""Train the active models and persist predictions for upcoming fixtures.

Usage:
    python -m app.jobs.train_models
"""

from __future__ import annotations

import asyncio
import sys
from datetime import UTC, datetime

import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import configure_logging, get_logger
from app.db import AsyncSessionLocal
from app.db.models import Match, Prediction
from app.features.drivers import build_drivers
from app.features.narrative import generate_narrative
from app.models import DixonColesModel, EnsembleModel
from app.models.bayesian import BayesianModel
from app.models.xgboost_model import XGBoostModel


async def run() -> int:
    configure_logging()
    log = get_logger(__name__)

    async with AsyncSessionLocal() as db:
        log.info("train.start")
        matches_df = await _load_historical_matches(db)

        if matches_df.empty:
            log.warning("train.no_matches")
            return 0

        # Build & fit ensemble
        dc = DixonColesModel()
        xgb = XGBoostModel()
        bayes = BayesianModel()
        xgb.set_fallback(dc)
        bayes.set_fallback(dc)

        ensemble = EnsembleModel(members=[(dc, 1.0), (xgb, 0.0), (bayes, 0.0)])
        ensemble.fit(matches_df)
        log.info("train.fitted", n_matches=len(matches_df))

        # Predict upcoming fixtures
        upcoming = await _load_upcoming_fixtures(db)
        log.info("train.predicting", n_upcoming=len(upcoming))

        written = 0
        for fixture in upcoming:
            home_name = fixture.home_team.short_name
            away_name = fixture.away_team.short_name
            try:
                pred = ensemble.predict_match(home_name, away_name)
            except Exception as e:
                log.warning(
                    "train.predict_failed",
                    home=home_name,
                    away=away_name,
                    error=str(e),
                )
                continue

            drivers = build_drivers(home_name, away_name, pred, matches_df)
            narrative = generate_narrative(home_name, away_name, pred, drivers)

            await _upsert_prediction(db, fixture.id, "ensemble", pred, drivers, narrative)
            written += 1

        await db.commit()
        log.info("train.done", predictions_written=written)
    return 0


async def _load_historical_matches(db: AsyncSession) -> pd.DataFrame:
    """Load finished matches as a DataFrame ready for fitting."""
    stmt = (
        select(Match)
        .where(Match.status == "FINISHED")
        .options(selectinload(Match.home_team), selectinload(Match.away_team))
    )
    matches = (await db.execute(stmt)).scalars().all()
    rows = []
    for m in matches:
        if m.home_score is None or m.away_score is None:
            continue
        rows.append(
            {
                "home_team": m.home_team.short_name,
                "away_team": m.away_team.short_name,
                "home_score": m.home_score,
                "away_score": m.away_score,
                "date": m.kickoff,
                "match_id": m.id,
            }
        )
    return pd.DataFrame(rows)


async def _load_upcoming_fixtures(db: AsyncSession) -> list[Match]:
    stmt = (
        select(Match)
        .where(
            Match.status.in_(["SCHEDULED", "LIVE"]),
            Match.kickoff >= datetime.now(UTC),
        )
        .order_by(Match.kickoff.asc())
        .options(selectinload(Match.home_team), selectinload(Match.away_team))
    )
    return list((await db.execute(stmt)).scalars().all())


async def _upsert_prediction(
    db: AsyncSession,
    match_id: int,
    model_name: str,
    pred,
    drivers: list[dict],
    narrative: str,
) -> None:
    stmt = select(Prediction).where(
        Prediction.match_id == match_id, Prediction.model_name == model_name
    )
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        existing.prob_home = pred.prob_home
        existing.prob_draw = pred.prob_draw
        existing.prob_away = pred.prob_away
        existing.home_xg = pred.home_xg
        existing.away_xg = pred.away_xg
        existing.prob_btts = pred.prob_btts
        existing.prob_over_2_5 = pred.prob_over_2_5
        existing.scoreline_distribution = pred.scoreline_distribution
        existing.drivers = drivers
        existing.narrative = narrative
        return

    row = Prediction(
        match_id=match_id,
        model_name=model_name,
        prob_home=pred.prob_home,
        prob_draw=pred.prob_draw,
        prob_away=pred.prob_away,
        home_xg=pred.home_xg,
        away_xg=pred.away_xg,
        prob_btts=pred.prob_btts,
        prob_over_2_5=pred.prob_over_2_5,
        scoreline_distribution=pred.scoreline_distribution,
        drivers=drivers,
        narrative=narrative,
    )
    db.add(row)


if __name__ == "__main__":
    sys.exit(asyncio.run(run()))
