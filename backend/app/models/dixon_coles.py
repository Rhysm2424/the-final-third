"""Dixon-Coles model.

A Poisson-based bivariate scoring model with a low-score correlation
adjustment to better capture the empirical 0-0 / 1-0 / 0-1 / 1-1
frequencies in football. Estimated by maximum likelihood with
exponential time-weighting.

References:
    Dixon & Coles (1997), "Modelling Association Football Scores and
    Inefficiencies in the Football Betting Market".
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import poisson

from app.models.base import BaseModel, MatchPrediction

MAX_GOALS = 8  # truncation for the scoreline matrix


@dataclass
class DixonColesParams:
    """Fitted parameters."""

    attack: dict[str, float] = field(default_factory=dict)
    defense: dict[str, float] = field(default_factory=dict)
    home_advantage: float = 0.25
    rho: float = -0.10  # low-score correlation
    fitted: bool = False


def _tau(home_goals: int, away_goals: int, lambda_h: float, lambda_a: float, rho: float) -> float:
    """Low-score correlation adjustment."""
    if home_goals == 0 and away_goals == 0:
        return 1.0 - lambda_h * lambda_a * rho
    if home_goals == 0 and away_goals == 1:
        return 1.0 + lambda_h * rho
    if home_goals == 1 and away_goals == 0:
        return 1.0 + lambda_a * rho
    if home_goals == 1 and away_goals == 1:
        return 1.0 - rho
    return 1.0


class DixonColesModel(BaseModel):
    name = "dixon_coles"

    def __init__(self, xi: float = 0.0018) -> None:
        """xi is the time-decay parameter (per day)."""
        self.xi = xi
        self.params = DixonColesParams()

    @property
    def is_fitted(self) -> bool:
        return self.params.fitted

    # ------------------------------------------------------------------
    # Fit
    # ------------------------------------------------------------------

    def fit(self, matches: pd.DataFrame) -> None:
        """Fit the model on historical matches.

        Required columns: home_team, away_team, home_score, away_score, date.
        """
        df = matches.copy()
        df = df.dropna(subset=["home_score", "away_score"])
        if df.empty:
            raise ValueError("No matches to fit on")

        df["home_score"] = df["home_score"].astype(int)
        df["away_score"] = df["away_score"].astype(int)
        df["date"] = pd.to_datetime(df["date"])
        max_date = df["date"].max()
        df["weight"] = np.exp(-self.xi * (max_date - df["date"]).dt.days)

        teams = sorted(set(df["home_team"]).union(df["away_team"]))
        n_teams = len(teams)
        team_index = {t: i for i, t in enumerate(teams)}

        # Parameter vector layout:
        # [attack_0, ..., attack_{n-1}, defense_0, ..., defense_{n-1}, home_adv, rho]
        # Constraint: mean(attack) = 0 — enforced via re-parameterisation.
        # We let attack[0..n-2] be free, attack[n-1] = -sum(attack[0..n-2]).

        def unpack(x: np.ndarray) -> tuple[np.ndarray, np.ndarray, float, float]:
            atk_free = x[: n_teams - 1]
            atk_last = -atk_free.sum()
            attack = np.append(atk_free, atk_last)
            defense = x[n_teams - 1 : 2 * n_teams - 1]
            home_adv = x[2 * n_teams - 1]
            rho = x[2 * n_teams]
            return attack, defense, home_adv, rho

        home_idx = df["home_team"].map(team_index).to_numpy()
        away_idx = df["away_team"].map(team_index).to_numpy()
        hs = df["home_score"].to_numpy()
        as_ = df["away_score"].to_numpy()
        w = df["weight"].to_numpy()

        def neg_log_likelihood(x: np.ndarray) -> float:
            attack, defense, home_adv, rho = unpack(x)
            # lambda_h = exp(attack_home + defense_away + home_adv)
            # lambda_a = exp(attack_away + defense_home)
            lh = np.exp(attack[home_idx] + defense[away_idx] + home_adv)
            la = np.exp(attack[away_idx] + defense[home_idx])
            # Clamp to avoid numerical blow-ups
            lh = np.clip(lh, 1e-6, 10.0)
            la = np.clip(la, 1e-6, 10.0)

            ll_h = hs * np.log(lh) - lh
            ll_a = as_ * np.log(la) - la

            # tau adjustment for low scores
            tau = np.ones_like(lh)
            mask_00 = (hs == 0) & (as_ == 0)
            mask_01 = (hs == 0) & (as_ == 1)
            mask_10 = (hs == 1) & (as_ == 0)
            mask_11 = (hs == 1) & (as_ == 1)
            tau[mask_00] = 1.0 - lh[mask_00] * la[mask_00] * rho
            tau[mask_01] = 1.0 + lh[mask_01] * rho
            tau[mask_10] = 1.0 + la[mask_10] * rho
            tau[mask_11] = 1.0 - rho
            tau = np.clip(tau, 1e-6, None)

            ll = w * (ll_h + ll_a + np.log(tau))
            return float(-ll.sum())

        # Initial guess
        x0 = np.concatenate(
            [
                np.zeros(n_teams - 1),  # attacks
                np.zeros(n_teams),  # defenses
                [0.25, -0.10],  # home_adv, rho
            ]
        )

        bounds = [(-3.0, 3.0)] * (n_teams - 1) + [(-3.0, 3.0)] * n_teams + [(0.0, 1.0), (-0.5, 0.5)]

        result = minimize(
            neg_log_likelihood,
            x0,
            method="L-BFGS-B",
            bounds=bounds,
            options={"maxiter": 200},
        )

        attack, defense, home_adv, rho = unpack(result.x)

        self.params = DixonColesParams(
            attack={t: float(attack[i]) for t, i in team_index.items()},
            defense={t: float(defense[i]) for t, i in team_index.items()},
            home_advantage=float(home_adv),
            rho=float(rho),
            fitted=True,
        )

    # ------------------------------------------------------------------
    # Predict
    # ------------------------------------------------------------------

    def predict_match(self, home_team: str, away_team: str) -> MatchPrediction:
        if not self.is_fitted:
            raise RuntimeError("Model is not fitted")

        atk_h = self.params.attack.get(home_team, 0.0)
        atk_a = self.params.attack.get(away_team, 0.0)
        def_h = self.params.defense.get(home_team, 0.0)
        def_a = self.params.defense.get(away_team, 0.0)
        ha = self.params.home_advantage
        rho = self.params.rho

        lambda_h = float(np.exp(atk_h + def_a + ha))
        lambda_a = float(np.exp(atk_a + def_h))

        # Scoreline matrix
        h_pmf = poisson.pmf(np.arange(MAX_GOALS + 1), lambda_h)
        a_pmf = poisson.pmf(np.arange(MAX_GOALS + 1), lambda_a)
        score_matrix = np.outer(h_pmf, a_pmf)

        # Apply tau adjustment to low scores
        score_matrix[0, 0] *= 1.0 - lambda_h * lambda_a * rho
        score_matrix[0, 1] *= 1.0 + lambda_h * rho
        score_matrix[1, 0] *= 1.0 + lambda_a * rho
        score_matrix[1, 1] *= 1.0 - rho

        # Renormalise (tau breaks unity slightly)
        score_matrix = np.clip(score_matrix, 0.0, None)
        total = score_matrix.sum()
        if total > 0:
            score_matrix /= total

        # 1X2
        prob_home = float(np.tril(score_matrix, -1).sum())
        prob_draw = float(np.trace(score_matrix))
        prob_away = float(np.triu(score_matrix, 1).sum())

        # BTTS — both score ≥ 1
        prob_btts = float(score_matrix[1:, 1:].sum())

        # Over 2.5
        total_goals_matrix = np.arange(MAX_GOALS + 1)[:, None] + np.arange(MAX_GOALS + 1)[None, :]
        prob_over_2_5 = float(score_matrix[total_goals_matrix > 2.5].sum())

        # Top-12 scoreline distribution
        flat = score_matrix.flatten()
        top_idx = np.argsort(flat)[::-1][:12]
        top_scorelines: list[dict] = []
        for idx in top_idx:
            h, a = divmod(int(idx), MAX_GOALS + 1)
            top_scorelines.append({"home": h, "away": a, "prob": float(flat[idx])})

        return MatchPrediction(
            prob_home=prob_home,
            prob_draw=prob_draw,
            prob_away=prob_away,
            home_xg=lambda_h,
            away_xg=lambda_a,
            prob_btts=prob_btts,
            prob_over_2_5=prob_over_2_5,
            scoreline_distribution=top_scorelines,
        )
