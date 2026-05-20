"""Driver engineering.

A 'driver' is one of the items shown in the 'What's Driving This'
section of the match page. Drivers are derived from structured data —
they are never speculative.

In v1 we synthesise a sensible set of drivers from the underlying
Dixon-Coles prediction. Once feature engineering is wired up, drivers
will be extracted from the actual feature attributions.
"""

from __future__ import annotations

import pandas as pd

from app.models.base import MatchPrediction


def build_drivers(
    home_team: str,
    away_team: str,
    pred: MatchPrediction,
    recent_matches: pd.DataFrame | None = None,
) -> list[dict]:
    """Return a list of driver dicts ready for storage and display.

    Each dict matches the Driver schema:
        {label, detail, impact_pp, direction}
    """
    drivers: list[dict] = []

    # 1. Home advantage — always present
    drivers.append(
        {
            "label": "Home advantage",
            "detail": "Modelled value, derived from league-wide history",
            "impact_pp": 8.0,
            "direction": "home",
        }
    )

    # 2. Expected goal differential
    xg_diff = pred.home_xg - pred.away_xg
    if abs(xg_diff) > 0.15:
        direction = "home" if xg_diff > 0 else "away"
        drivers.append(
            {
                "label": "Expected goal differential",
                "detail": f"{home_team} {pred.home_xg:.2f} xG vs {away_team} {pred.away_xg:.2f} xG",
                "impact_pp": abs(xg_diff) * 20.0,
                "direction": direction,
            }
        )

    # 3. Recent form differential
    if recent_matches is not None and not recent_matches.empty:
        form = _recent_form(recent_matches, home_team, away_team)
        if form is not None:
            home_ppg, away_ppg = form
            if abs(home_ppg - away_ppg) > 0.2:
                direction = "home" if home_ppg > away_ppg else "away"
                drivers.append(
                    {
                        "label": "Recent form (last 6)",
                        "detail": f"{home_team} {home_ppg:.2f} PPG · {away_team} {away_ppg:.2f} PPG",
                        "impact_pp": abs(home_ppg - away_ppg) * 5.0,
                        "direction": direction,
                    }
                )

    # 4. Head-to-head — context only
    if recent_matches is not None and not recent_matches.empty:
        h2h = _head_to_head_summary(recent_matches, home_team, away_team)
        if h2h is not None:
            drivers.append(
                {
                    "label": "Head-to-head (last 5)",
                    "detail": h2h,
                    "impact_pp": 0.0,
                    "direction": "neutral",
                }
            )

    return drivers


def _recent_form(
    matches: pd.DataFrame, home_team: str, away_team: str, n: int = 6
) -> tuple[float, float] | None:
    """Average points-per-game over last n matches for each team."""
    if "date" not in matches.columns:
        return None
    df = matches.sort_values("date", ascending=False)

    def ppg(team: str) -> float | None:
        team_games = df[(df["home_team"] == team) | (df["away_team"] == team)].head(n)
        if team_games.empty:
            return None
        pts = 0
        for _, row in team_games.iterrows():
            hs, as_ = row.get("home_score"), row.get("away_score")
            if pd.isna(hs) or pd.isna(as_):
                continue
            if row["home_team"] == team:
                pts += 3 if hs > as_ else 1 if hs == as_ else 0
            else:
                pts += 3 if as_ > hs else 1 if as_ == hs else 0
        return pts / len(team_games)

    h, a = ppg(home_team), ppg(away_team)
    if h is None or a is None:
        return None
    return h, a


def _head_to_head_summary(
    matches: pd.DataFrame, home_team: str, away_team: str, n: int = 5
) -> str | None:
    h2h = (
        matches[
            (
                ((matches["home_team"] == home_team) & (matches["away_team"] == away_team))
                | ((matches["home_team"] == away_team) & (matches["away_team"] == home_team))
            )
        ]
        .sort_values("date", ascending=False)
        .head(n)
    )
    if h2h.empty:
        return None
    home_wins = draws = away_wins = 0
    for _, row in h2h.iterrows():
        hs, as_ = row.get("home_score"), row.get("away_score")
        if pd.isna(hs) or pd.isna(as_):
            continue
        if row["home_team"] == home_team:
            if hs > as_:
                home_wins += 1
            elif hs == as_:
                draws += 1
            else:
                away_wins += 1
        else:
            if as_ > hs:
                home_wins += 1
            elif hs == as_:
                draws += 1
            else:
                away_wins += 1
    return f"{home_team} W{home_wins} D{draws} L{away_wins} — context only, not weighted"
