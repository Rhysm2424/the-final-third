"""Ensemble model — weighted combination of base models.

Until the XGBoost and Bayesian models are trained, the ensemble passes
Dixon-Coles through unchanged (weights are auto-redistributed away
from unfitted models).
"""

from __future__ import annotations

import pandas as pd

from app.models.base import BaseModel, MatchPrediction


class EnsembleModel(BaseModel):
    name = "ensemble"

    def __init__(
        self,
        members: list[tuple[BaseModel, float]],
    ) -> None:
        """members is a list of (model, weight) pairs. Weights need not sum to 1."""
        if not members:
            raise ValueError("Ensemble needs at least one member")
        self.members = members

    @property
    def is_fitted(self) -> bool:
        return any(m.is_fitted for m, _ in self.members)

    def fit(self, matches: pd.DataFrame) -> None:
        for m, _ in self.members:
            try:
                m.fit(matches)
            except NotImplementedError:
                continue

    def predict_match(self, home_team: str, away_team: str) -> MatchPrediction:
        active = [(m, w) for m, w in self.members if m.is_fitted]
        if not active:
            raise RuntimeError("Ensemble has no fitted members")

        total_w = sum(w for _, w in active)
        preds = [(m.predict_match(home_team, away_team), w / total_w) for m, w in active]

        ph = sum(p.prob_home * w for p, w in preds)
        pd_ = sum(p.prob_draw * w for p, w in preds)
        pa = sum(p.prob_away * w for p, w in preds)

        # Renormalise in case of rounding
        s = ph + pd_ + pa
        ph, pd_, pa = ph / s, pd_ / s, pa / s

        hxg = sum(p.home_xg * w for p, w in preds)
        axg = sum(p.away_xg * w for p, w in preds)

        # BTTS / O2.5 — average where present
        btts_vals = [(p.prob_btts, w) for p, w in preds if p.prob_btts is not None]
        o25_vals = [(p.prob_over_2_5, w) for p, w in preds if p.prob_over_2_5 is not None]
        prob_btts = (
            sum(v * w for v, w in btts_vals) / sum(w for _, w in btts_vals) if btts_vals else None
        )
        prob_o25 = (
            sum(v * w for v, w in o25_vals) / sum(w for _, w in o25_vals) if o25_vals else None
        )

        # Scoreline distribution — take from the most-weighted member that has one
        scorelines = next(
            (p.scoreline_distribution for p, _ in preds if p.scoreline_distribution),
            None,
        )

        return MatchPrediction(
            prob_home=ph,
            prob_draw=pd_,
            prob_away=pa,
            home_xg=hxg,
            away_xg=axg,
            prob_btts=prob_btts,
            prob_over_2_5=prob_o25,
            scoreline_distribution=scorelines,
        )
