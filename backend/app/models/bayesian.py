"""Bayesian hierarchical model (PyMC) — SCAFFOLD.

A future iteration will use PyMC to fit a hierarchical Poisson model
with team strength priors. For v1 this is a placeholder that defers
to a fallback model.

PyMC is not in the v1 dependency set to keep install time down. Add
`pymc>=5.18.0` to pyproject.toml when activating this model.
"""

from __future__ import annotations

import pandas as pd

from app.models.base import BaseModel, MatchPrediction


class BayesianModel(BaseModel):
    name = "bayesian"

    def __init__(self) -> None:
        self._fitted = False
        self._fallback: BaseModel | None = None

    @property
    def is_fitted(self) -> bool:
        return self._fitted

    def set_fallback(self, fallback: BaseModel) -> None:
        self._fallback = fallback

    def fit(self, matches: pd.DataFrame) -> None:
        raise NotImplementedError(
            "Bayesian model not yet implemented. Add PyMC to dependencies "
            "and implement the hierarchical Poisson fit before activating."
        )

    def predict_match(self, home_team: str, away_team: str) -> MatchPrediction:
        if self._fallback is not None:
            return self._fallback.predict_match(home_team, away_team)
        raise RuntimeError("Bayesian model unavailable and no fallback set.")
