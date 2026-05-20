"""Abstract base class for prediction models.

Every model — Dixon-Coles, XGBoost, PyMC Bayesian, the ensemble itself —
implements this interface. That's what makes them stackable.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import pandas as pd


@dataclass
class MatchPrediction:
    """The standard output shape for a single match prediction."""

    prob_home: float
    prob_draw: float
    prob_away: float
    home_xg: float
    away_xg: float
    prob_btts: float | None = None
    prob_over_2_5: float | None = None
    scoreline_distribution: list[dict] | None = None  # [{home, away, prob}]

    def to_dict(self) -> dict:
        return {
            "prob_home": self.prob_home,
            "prob_draw": self.prob_draw,
            "prob_away": self.prob_away,
            "home_xg": self.home_xg,
            "away_xg": self.away_xg,
            "prob_btts": self.prob_btts,
            "prob_over_2_5": self.prob_over_2_5,
            "scoreline_distribution": self.scoreline_distribution,
        }


class BaseModel(ABC):
    """Abstract prediction model.

    Subclasses must implement `fit` and `predict_match`. They may override
    `predict_batch` for vectorised efficiency.
    """

    name: str = "base"

    @abstractmethod
    def fit(self, matches: pd.DataFrame) -> None:
        """Train the model on a DataFrame of historical matches.

        Expected columns: home_team, away_team, home_score, away_score, date.
        """
        ...

    @abstractmethod
    def predict_match(self, home_team: str, away_team: str) -> MatchPrediction:
        """Predict a single fixture."""
        ...

    def predict_batch(self, fixtures: list[tuple[str, str]]) -> list[MatchPrediction]:
        """Predict a list of (home_team, away_team) tuples."""
        return [self.predict_match(h, a) for h, a in fixtures]

    @property
    def is_fitted(self) -> bool:
        return False
