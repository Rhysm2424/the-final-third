"""Tests for the Dixon-Coles model."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from app.models.dixon_coles import DixonColesModel


@pytest.fixture
def synthetic_matches() -> pd.DataFrame:
    """A small synthetic dataset with a clearly-strong team."""
    rng = np.random.default_rng(42)
    teams = ["StrongA", "StrongB", "MidC", "WeakD"]
    strength = {"StrongA": 1.8, "StrongB": 1.5, "MidC": 1.0, "WeakD": 0.7}
    rows = []
    for _ in range(200):
        h, a = rng.choice(teams, size=2, replace=False)
        lh = strength[h] * 1.2  # home advantage
        la = strength[a]
        rows.append(
            {
                "home_team": h,
                "away_team": a,
                "home_score": int(rng.poisson(lh)),
                "away_score": int(rng.poisson(la)),
                "date": pd.Timestamp("2024-01-01") + pd.Timedelta(days=int(rng.integers(0, 200))),
            }
        )
    return pd.DataFrame(rows)


def test_fit_then_predict(synthetic_matches: pd.DataFrame) -> None:
    model = DixonColesModel()
    model.fit(synthetic_matches)
    assert model.is_fitted

    pred = model.predict_match("StrongA", "WeakD")
    # Probabilities sum to ~1
    total = pred.prob_home + pred.prob_draw + pred.prob_away
    assert abs(total - 1.0) < 1e-6
    # Strong-home vs weak-away — home should be heavily favoured
    assert pred.prob_home > pred.prob_away
    # xG positive
    assert pred.home_xg > 0
    assert pred.away_xg > 0


def test_top_scorelines_present(synthetic_matches: pd.DataFrame) -> None:
    model = DixonColesModel()
    model.fit(synthetic_matches)
    pred = model.predict_match("StrongA", "MidC")
    assert pred.scoreline_distribution is not None
    assert len(pred.scoreline_distribution) == 12
    # Sorted descending by probability
    probs = [s["prob"] for s in pred.scoreline_distribution]
    assert probs == sorted(probs, reverse=True)


def test_unfitted_raises() -> None:
    model = DixonColesModel()
    with pytest.raises(RuntimeError):
        model.predict_match("A", "B")
