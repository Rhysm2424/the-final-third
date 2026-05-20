"""Walk-forward backtest harness with calibration and P&L simulation."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from app.models.base import BaseModel


@dataclass
class BacktestResult:
    model_name: str
    season_start: int
    season_end: int
    n_predictions: int
    brier_score: float
    log_loss: float
    top_pick_accuracy: float
    market_brier: float | None
    market_log_loss: float | None
    calibration_bins: list[dict] = field(default_factory=list)
    simulated_pnl_units: float | None = None
    simulated_roi_pct: float | None = None


def _multi_brier(probs: np.ndarray, outcomes: np.ndarray) -> float:
    """Multi-class Brier score. outcomes is (n,3) one-hot."""
    return float(np.mean(np.sum((probs - outcomes) ** 2, axis=1)))


def _multi_log_loss(probs: np.ndarray, outcomes: np.ndarray, eps: float = 1e-12) -> float:
    p = np.clip(probs, eps, 1 - eps)
    return float(-np.mean(np.sum(outcomes * np.log(p), axis=1)))


def _calibration_bins(probs: np.ndarray, outcomes: np.ndarray, n_bins: int = 10) -> list[dict]:
    """Bin by predicted probability of the *picked* outcome.

    For each prediction we take p_max (the picked outcome) and whether it
    materialised. Bin those into n_bins equal-width buckets.
    """
    pick_idx = probs.argmax(axis=1)
    pick_p = probs[np.arange(len(probs)), pick_idx]
    pick_hit = outcomes[np.arange(len(outcomes)), pick_idx]

    bins = np.linspace(0.0, 1.0, n_bins + 1)
    out: list[dict] = []
    for i in range(n_bins):
        lo, hi = bins[i], bins[i + 1]
        mask = (pick_p >= lo) & (pick_p < hi) if i < n_bins - 1 else (pick_p >= lo) & (pick_p <= hi)
        n = int(mask.sum())
        if n == 0:
            continue
        out.append(
            {
                "bin_lower": float(lo),
                "bin_upper": float(hi),
                "predicted": float(pick_p[mask].mean()),
                "actual": float(pick_hit[mask].mean()),
                "count": n,
            }
        )
    return out


def _odds_to_probs(o_h: float, o_d: float, o_a: float) -> np.ndarray | None:
    """Convert decimal odds to implied probabilities (overround removed)."""
    if any(o is None or o <= 1.01 for o in (o_h, o_d, o_a)):
        return None
    raw = np.array([1 / o_h, 1 / o_d, 1 / o_a])
    return raw / raw.sum()


def _simulate_pnl(probs: np.ndarray, outcomes: np.ndarray, odds: np.ndarray) -> tuple[float, float]:
    """Flat-stake 1 unit on the model's pick whenever its probability
    exceeds the implied market probability by at least 2 percentage points.

    Returns (total_pnl_units, roi_pct).
    """
    pick_idx = probs.argmax(axis=1)
    pick_p = probs[np.arange(len(probs)), pick_idx]
    pick_hit = outcomes[np.arange(len(outcomes)), pick_idx]
    pick_odds = odds[np.arange(len(odds)), pick_idx]

    # Implied prob from odds
    implied = 1.0 / pick_odds
    edge_mask = pick_p - implied > 0.02

    if edge_mask.sum() == 0:
        return 0.0, 0.0

    stakes = edge_mask.astype(float)  # 1 unit each
    payouts = np.where(pick_hit == 1, pick_odds, 0.0)
    pnl = (payouts - 1.0) * stakes
    total_pnl = float(pnl.sum())
    total_staked = float(stakes.sum())
    roi = (total_pnl / total_staked * 100) if total_staked > 0 else 0.0
    return total_pnl, roi


def walk_forward_backtest(
    model: BaseModel,
    matches: pd.DataFrame,
    train_start_season: int,
    test_seasons: list[int],
    season_col: str = "season",
    refit_each_season: bool = True,
) -> BacktestResult:
    """Walk-forward backtest.

    For each test season, fit on everything before it and predict every match.
    Matches DataFrame must contain: home_team, away_team, home_score,
    away_score, date, season, [odds_home, odds_draw, odds_away].
    """
    required = {"home_team", "away_team", "home_score", "away_score", "date", season_col}
    missing = required - set(matches.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df = matches.dropna(subset=["home_score", "away_score"]).copy()

    all_probs: list[list[float]] = []
    all_outcomes: list[list[int]] = []
    all_odds: list[list[float]] = []
    has_odds = {"odds_home", "odds_draw", "odds_away"}.issubset(df.columns)

    for test_season in sorted(test_seasons):
        train = df[df[season_col] < test_season]
        train = train[train[season_col] >= train_start_season]
        test = df[df[season_col] == test_season]

        if train.empty or test.empty:
            continue

        if refit_each_season or not model.is_fitted:
            model.fit(train)

        for _, row in test.iterrows():
            try:
                pred = model.predict_match(row["home_team"], row["away_team"])
            except Exception:
                continue
            all_probs.append([pred.prob_home, pred.prob_draw, pred.prob_away])

            hs, as_ = int(row["home_score"]), int(row["away_score"])
            if hs > as_:
                outcome = [1, 0, 0]
            elif hs == as_:
                outcome = [0, 1, 0]
            else:
                outcome = [0, 0, 1]
            all_outcomes.append(outcome)

            if has_odds:
                all_odds.append([row["odds_home"], row["odds_draw"], row["odds_away"]])

    if not all_probs:
        raise RuntimeError("No predictions produced during backtest")

    probs = np.array(all_probs)
    outcomes = np.array(all_outcomes)

    brier = _multi_brier(probs, outcomes)
    ll = _multi_log_loss(probs, outcomes)
    top_acc = float((probs.argmax(axis=1) == outcomes.argmax(axis=1)).mean())
    calib = _calibration_bins(probs, outcomes)

    market_brier: float | None = None
    market_log_loss: float | None = None
    pnl: float | None = None
    roi: float | None = None
    if has_odds and all_odds:
        odds_arr = np.array(all_odds, dtype=float)
        # Filter rows with valid odds
        valid = np.all(odds_arr > 1.01, axis=1) & ~np.any(np.isnan(odds_arr), axis=1)
        if valid.sum() > 0:
            market_probs = np.zeros_like(probs[valid])
            for i, (oh, od, oa) in enumerate(odds_arr[valid]):
                ip = _odds_to_probs(oh, od, oa)
                if ip is not None:
                    market_probs[i] = ip
            market_brier = _multi_brier(market_probs, outcomes[valid])
            market_log_loss = _multi_log_loss(market_probs, outcomes[valid])
            pnl, roi = _simulate_pnl(probs[valid], outcomes[valid], odds_arr[valid])

    return BacktestResult(
        model_name=model.name,
        season_start=min(test_seasons),
        season_end=max(test_seasons),
        n_predictions=len(probs),
        brier_score=brier,
        log_loss=ll,
        top_pick_accuracy=top_acc,
        market_brier=market_brier,
        market_log_loss=market_log_loss,
        calibration_bins=calib,
        simulated_pnl_units=pnl,
        simulated_roi_pct=roi,
    )
