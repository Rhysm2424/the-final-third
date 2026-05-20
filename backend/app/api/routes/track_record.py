"""Track record — the receipts page."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.schemas import (
    CalibrationBin,
    PastPredictionRow,
    TrackRecordResponse,
    TrackRecordSummary,
)
from app.db import get_db
from app.db.models import BacktestRun, Match, Prediction

router = APIRouter()


@router.get("", response_model=TrackRecordResponse)
async def get_track_record(db: AsyncSession = Depends(get_db)) -> TrackRecordResponse:
    # Pick the most recent ensemble backtest (or any latest)
    bt_stmt = select(BacktestRun).order_by(BacktestRun.created_at.desc()).limit(1)
    bt = (await db.execute(bt_stmt)).scalar_one_or_none()

    summary = _summary_from_backtest(bt)

    # Recent predictions on finished matches
    cutoff = datetime.now(UTC) - timedelta(days=60)
    rec_stmt = (
        select(Prediction)
        .join(Match, Prediction.match_id == Match.id)
        .where(
            Match.kickoff >= cutoff,
            Match.status == "FINISHED",
        )
        .order_by(Match.kickoff.desc())
        .limit(15)
        .options(
            selectinload(Prediction.match).selectinload(Match.home_team),
            selectinload(Prediction.match).selectinload(Match.away_team),
        )
    )
    preds = (await db.execute(rec_stmt)).scalars().all()

    recent = [_to_past_row(p) for p in preds]

    return TrackRecordResponse(summary=summary, recent=recent)


def _summary_from_backtest(bt: BacktestRun | None) -> TrackRecordSummary:
    if bt is None:
        return TrackRecordSummary(
            n_predictions=0,
            brier_score=0.0,
            log_loss=0.0,
            top_pick_accuracy=0.0,
            market_brier=None,
            market_log_loss=None,
            simulated_pnl_units=None,
            simulated_roi_pct=None,
            calibration_bins=[],
            model_name="—",
            season_range="—",
        )
    bins = [CalibrationBin(**b) for b in bt.calibration_bins]
    return TrackRecordSummary(
        n_predictions=bt.n_predictions,
        brier_score=bt.brier_score,
        log_loss=bt.log_loss,
        top_pick_accuracy=bt.top_pick_accuracy,
        market_brier=bt.market_brier,
        market_log_loss=bt.market_log_loss,
        simulated_pnl_units=bt.simulated_pnl_units,
        simulated_roi_pct=bt.simulated_roi_pct,
        calibration_bins=bins,
        model_name=bt.model_name,
        season_range=f"{bt.season_start}–{bt.season_end}",
    )


def _to_past_row(p: Prediction) -> PastPredictionRow:
    m = p.match
    pick, pick_prob = _argmax_pick(p.prob_home, p.prob_draw, p.prob_away)
    pick_label = (
        m.home_team.short_name
        if pick == "home"
        else m.away_team.short_name
        if pick == "away"
        else "Draw"
    )
    result = _grade_pick(pick, m.home_score, m.away_score)
    return PastPredictionRow(
        match_id=m.id,
        date=m.kickoff,
        home_team=m.home_team.short_name,
        away_team=m.away_team.short_name,
        home_score=m.home_score,
        away_score=m.away_score,
        pick=pick,
        pick_label=pick_label,
        pick_probability=pick_prob,
        result=result,
    )


def _argmax_pick(ph: float, pd: float, pa: float) -> tuple[str, float]:
    probs = {"home": ph, "draw": pd, "away": pa}
    best = max(probs, key=lambda k: probs[k])
    return best, probs[best]


def _grade_pick(pick: str, hs: int | None, as_: int | None) -> str:
    if hs is None or as_ is None:
        return "pending"
    if hs > as_:
        outcome = "home"
    elif hs < as_:
        outcome = "away"
    else:
        outcome = "draw"
    return "hit" if outcome == pick else "miss"
