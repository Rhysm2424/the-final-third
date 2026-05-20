"""Narrative generation from structured drivers.

This is templated, deterministic, and produces grammatical English from
the drivers list. When an LLM is wired in later, it will be constrained
to rephrase this output only — never to invent stats.
"""

from __future__ import annotations

from app.models.base import MatchPrediction


def generate_narrative(
    home_team: str,
    away_team: str,
    pred: MatchPrediction,
    drivers: list[dict],
) -> str:
    """Return a 2–3 sentence narrative summarising the prediction."""
    favourite_team, favourite_prob = _favourite(home_team, away_team, pred)
    if favourite_team == "Draw":
        leader = f"The model sees this match as too close to call, with a draw the most likely single outcome at {favourite_prob:.0%}."
    else:
        leader = (
            f"{favourite_team} are favoured at {favourite_prob:.0%}, with {pred.home_xg:.2f} "
            f"expected goals to {pred.away_xg:.2f}."
        )

    # Pick the most impactful non-neutral driver for the second sentence
    weighted = [d for d in drivers if d["direction"] != "neutral"]
    weighted.sort(key=lambda d: d["impact_pp"], reverse=True)

    secondary = ""
    if weighted:
        top = weighted[0]
        secondary = f" The biggest driver is {top['label'].lower()} — {top['detail']}."

    tertiary = ""
    btts_high = pred.prob_btts is not None and pred.prob_btts > 0.65
    btts_low = pred.prob_btts is not None and pred.prob_btts < 0.40
    over_high = pred.prob_over_2_5 is not None and pred.prob_over_2_5 > 0.60
    over_low = pred.prob_over_2_5 is not None and pred.prob_over_2_5 < 0.40

    if over_high and btts_high:
        tertiary = " Expect goals at both ends."
    elif over_low and btts_low:
        tertiary = " The model expects a low-scoring, tight affair."
    elif over_high:
        tertiary = " Goals look likely overall."

    return leader + secondary + tertiary


def _favourite(home_team: str, away_team: str, pred: MatchPrediction) -> tuple[str, float]:
    probs = {home_team: pred.prob_home, "Draw": pred.prob_draw, away_team: pred.prob_away}
    best = max(probs, key=lambda k: probs[k])
    return best, probs[best]
