"""XGBoost match outcome model — SCAFFOLD.

This is a placeholder that conforms to the BaseModel interface so the
ensemble has something to call. It is intentionally not active in v1.
Once feature engineering is built (`app/features/`), train this on
those features and the ensemble will pick it up automatically.
"""

from __future__ import annotations

import pandas as pd

from app.models.base import BaseModel, MatchPrediction


class XGBoostModel(BaseModel):
    name = "xgboost"

    def __init__(self) -> None:
        self._fitted = False
        self._fallback: BaseModel | None = None

    @property
    def is_fitted(self) -> bool:
        return self._fitted

    def set_fallback(self, fallback: BaseModel) -> None:
        """Until trained, defer to a fallback model (typically Dixon-Coles)."""
        self._fallback = fallback

    def fit(self, matches: pd.DataFrame) -> None:
        """Not implemented for v1. Will train on engineered features later."""
        raise NotImplementedError("XGBoost model not yet trained. Run feature engineering first.")

    def predict_match(self, home_team: str, away_team: str) -> MatchPrediction:
        if self._fallback is not None:
            return self._fallback.predict_match(home_team, away_team)
        raise RuntimeError(
            "XGBoost model unavailable and no fallback set. Wire Dixon-Coles "
            "as a fallback during ensemble construction."
        )
