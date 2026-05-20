"""Tests for the ensemble model."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from app.models.bayesian import BayesianModel
from app.models.dixon_coles import DixonColesModel
from app.models.ensemble import EnsembleModel
from app.models.xgboost_model import XGBoostModel


@pytest.fixture
def small_dataset() -> pd.DataFrame:
    rng = np.random.default_rng(0)
    teams = ["A", "B", "C"]
    rows = []
    for _ in range(80):
        h, a = rng.choice(teams, size=2, replace=False)
        rows.append(
            {
                "home_team": h,
                "away_team": a,
                "home_score": int(rng.poisson(1.4)),
                "away_score": int(rng.poisson(1.1)),
                "date": pd.Timestamp("2024-01-01") + pd.Timedelta(days=int(rng.integers(0, 100))),
            }
        )
    return pd.DataFrame(rows)


def test_ensemble_with_only_dixon_coles_fits_and_predicts(small_dataset: pd.DataFrame) -> None:
    dc = DixonColesModel()
    xgb = XGBoostModel()
    bayes = BayesianModel()
    xgb.set_fallback(dc)
    bayes.set_fallback(dc)

    ens = EnsembleModel(members=[(dc, 1.0), (xgb, 0.0), (bayes, 0.0)])
    ens.fit(small_dataset)
    assert ens.is_fitted

    pred = ens.predict_match("A", "B")
    total = pred.prob_home + pred.prob_draw + pred.prob_away
    assert abs(total - 1.0) < 1e-6


def test_ensemble_unfitted_members_skipped(small_dataset: pd.DataFrame) -> None:
    """An ensemble with unfitted non-Dixon members should still work."""
    dc = DixonColesModel()
    xgb = XGBoostModel()
    xgb.set_fallback(dc)

    ens = EnsembleModel(members=[(dc, 0.7), (xgb, 0.3)])
    ens.fit(small_dataset)
    pred = ens.predict_match("A", "C")
    assert 0 <= pred.prob_home <= 1
