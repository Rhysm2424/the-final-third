"""Tests for the backtest harness."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from app.models.backtest import walk_forward_backtest
from app.models.dixon_coles import DixonColesModel


@pytest.fixture
def two_seasons() -> pd.DataFrame:
    rng = np.random.default_rng(1)
    teams = ["A", "B", "C", "D"]
    rows = []
    for season in (2022, 2023):
        for _ in range(60):
            h, a = rng.choice(teams, size=2, replace=False)
            rows.append(
                {
                    "home_team": h,
                    "away_team": a,
                    "home_score": int(rng.poisson(1.3)),
                    "away_score": int(rng.poisson(1.1)),
                    "date": pd.Timestamp(f"{season}-08-01")
                    + pd.Timedelta(days=int(rng.integers(0, 250))),
                    "season": season,
                    "odds_home": 2.0,
                    "odds_draw": 3.4,
                    "odds_away": 3.6,
                }
            )
    return pd.DataFrame(rows)


def test_backtest_runs(two_seasons: pd.DataFrame) -> None:
    model = DixonColesModel()
    result = walk_forward_backtest(
        model,
        two_seasons,
        train_start_season=2022,
        test_seasons=[2023],
    )
    assert result.n_predictions > 0
    assert 0 <= result.brier_score <= 2.0
    assert result.log_loss > 0
    assert 0 <= result.top_pick_accuracy <= 1
    assert result.market_brier is not None
