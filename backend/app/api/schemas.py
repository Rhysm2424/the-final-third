"""Pydantic schemas. These are the API contract — kept in lockstep with the TS types in frontend/lib/types.ts."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ============================================================
# Team / Competition
# ============================================================


class TeamOut(ORMBase):
    id: int
    short_name: str
    full_name: str
    tla: str | None
    crest_url: str | None
    primary_color: str | None
    secondary_color: str | None
    is_premier_league: bool


class CompetitionOut(ORMBase):
    id: int
    code: str
    name: str
    tier: str


# ============================================================
# Match
# ============================================================


class MatchSummary(ORMBase):
    """Compact match row for fixture lists."""

    id: int
    kickoff: datetime
    matchday: int | None
    status: str
    home_team: TeamOut
    away_team: TeamOut
    competition: CompetitionOut
    home_score: int | None
    away_score: int | None
    # Top-line prediction probabilities for list display
    prob_home: float | None
    prob_draw: float | None
    prob_away: float | None


class ScorelineProb(BaseModel):
    home: int
    away: int
    prob: float


class Driver(BaseModel):
    label: str
    detail: str
    impact_pp: float  # in percentage points; sign carries meaning
    direction: str = Field(description="'home' | 'away' | 'neutral'")


class PredictionOut(ORMBase):
    id: int
    model_name: str
    prob_home: float
    prob_draw: float
    prob_away: float
    home_xg: float
    away_xg: float
    prob_btts: float | None
    prob_over_2_5: float | None
    scoreline_distribution: list[ScorelineProb] | None
    drivers: list[Driver] | None
    narrative: str | None
    created_at: datetime


class MatchDetail(ORMBase):
    """Full match page payload."""

    id: int
    kickoff: datetime
    matchday: int | None
    venue: str | None
    status: str
    home_team: TeamOut
    away_team: TeamOut
    competition: CompetitionOut
    home_score: int | None
    away_score: int | None
    home_xg: float | None
    away_xg: float | None
    odds_home: float | None
    odds_draw: float | None
    odds_away: float | None
    prediction: PredictionOut | None


# ============================================================
# Insights
# ============================================================


class InsightOut(ORMBase):
    id: int
    kind: str
    subject: str
    headline: str
    detail: str
    data: dict[str, Any]
    notability: float
    is_weighted: bool
    created_at: datetime


# ============================================================
# League projection
# ============================================================


class LeagueProjectionRow(ORMBase):
    team: TeamOut
    expected_position: float
    expected_points: float
    title_probability: float
    top_four_probability: float
    relegation_probability: float


class LeagueProjectionResponse(BaseModel):
    competition: CompetitionOut
    as_of: datetime
    rows: list[LeagueProjectionRow]


# ============================================================
# Track record
# ============================================================


class CalibrationBin(BaseModel):
    bin_lower: float
    bin_upper: float
    predicted: float
    actual: float
    count: int


class TrackRecordSummary(BaseModel):
    n_predictions: int
    brier_score: float
    log_loss: float
    top_pick_accuracy: float
    market_brier: float | None
    market_log_loss: float | None
    simulated_pnl_units: float | None
    simulated_roi_pct: float | None
    calibration_bins: list[CalibrationBin]
    model_name: str
    season_range: str


class PastPredictionRow(BaseModel):
    match_id: int
    date: datetime
    home_team: str
    away_team: str
    home_score: int | None
    away_score: int | None
    pick: str  # 'home' | 'draw' | 'away'
    pick_label: str  # human-readable team name or 'Draw'
    pick_probability: float
    result: str  # 'hit' | 'miss' | 'pending'


class TrackRecordResponse(BaseModel):
    summary: TrackRecordSummary
    recent: list[PastPredictionRow]


# ============================================================
# Health
# ============================================================


class HealthResponse(BaseModel):
    status: str
    demo_mode: bool
    version: str
