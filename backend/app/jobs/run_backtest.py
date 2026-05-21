"""Run a walk-forward backtest and persist the result.

Usage:
    python -m app.jobs.run_backtest
"""

from __future__ import annotations

import asyncio
import sys

import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import configure_logging, get_logger
from app.db import AsyncSessionLocal
from app.db.models import BacktestRun, Match
from app.models import DixonColesModel
from app.models.backtest import walk_forward_backtest


def _season_from_date(d) -> int:
    """Return the start-year of the season containing date d.

    A season runs Aug→May, so anything from August onwards is that year,
    anything before is the previous year.
    """
    return int(d.year) if d.month >= 8 else int(d.year) - 1


async def run() -> int:
    configure_logging()
    log = get_logger(__name__)

    async with AsyncSessionLocal() as db:
        df = await _load_finished_matches(db)
        if df.empty or len(df) < 100:
            log.warning("backtest.not_enough_data", rows=len(df))
            return 0

        df["season"] = df["date"].apply(_season_from_date)
        seasons = sorted(df["season"].unique())
        # Test on the most recent 2 seasons (or all but first if fewer)
        if len(seasons) < 2:
            log.warning("backtest.single_season")
            return 0

        train_start = seasons[0]
        test_seasons = seasons[-2:]

        model = DixonColesModel()
        result = walk_forward_backtest(
            model,
            df,
            train_start_season=train_start,
            test_seasons=test_seasons,
        )
        log.info(
            "backtest.done",
            model=result.model_name,
            n=result.n_predictions,
            brier=result.brier_score,
            log_loss=result.log_loss,
        )

        db.add(
            BacktestRun(
                model_name=result.model_name,
                season_start=result.season_start,
                season_end=result.season_end,
                n_predictions=result.n_predictions,
                brier_score=result.brier_score,
                log_loss=result.log_loss,
                top_pick_accuracy=result.top_pick_accuracy,
                market_brier=result.market_brier,
                market_log_loss=result.market_log_loss,
                calibration_bins=result.calibration_bins,
                simulated_pnl_units=result.simulated_pnl_units,
                simulated_roi_pct=result.simulated_roi_pct,
            )
        )
        await db.commit()
    return 0


async def _load_finished_matches(db: AsyncSession) -> pd.DataFrame:
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
                "odds_home": m.odds_home,
                "odds_draw": m.odds_draw,
                "odds_away": m.odds_away,
            }
        )
    return pd.DataFrame(rows)


if __name__ == "__main__":
    sys.exit(asyncio.run(run()))
