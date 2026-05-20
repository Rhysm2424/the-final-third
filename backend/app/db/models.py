"""ORM models — the schema in code."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Competition(Base):
    __tablename__ = "competitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    tier: Mapped[str] = mapped_column(String(32), nullable=False, default="LEAGUE")
    # LEAGUE | CUP | EUROPEAN | INTERNATIONAL

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    matches: Mapped[list[Match]] = relationship(back_populates="competition")


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    short_name: Mapped[str] = mapped_column(String(64), nullable=False)
    full_name: Mapped[str] = mapped_column(String(128), nullable=False)
    tla: Mapped[str | None] = mapped_column(String(8), nullable=True)
    crest_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    primary_color: Mapped[str | None] = mapped_column(String(16), nullable=True)
    secondary_color: Mapped[str | None] = mapped_column(String(16), nullable=True)
    is_premier_league: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint("short_name", name="uq_team_short_name"),)


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    external_id: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)

    competition_id: Mapped[int] = mapped_column(
        ForeignKey("competitions.id", ondelete="CASCADE"), nullable=False
    )
    home_team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE"), nullable=False
    )
    away_team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE"), nullable=False
    )

    kickoff: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    matchday: Mapped[int | None] = mapped_column(Integer, nullable=True)
    venue: Mapped[str | None] = mapped_column(String(128), nullable=True)

    status: Mapped[str] = mapped_column(String(32), default="SCHEDULED")
    # SCHEDULED | LIVE | FINISHED | POSTPONED | CANCELLED

    home_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    away_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # xG snapshots (post-match)
    home_xg: Mapped[float | None] = mapped_column(Float, nullable=True)
    away_xg: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Closing market odds for benchmark
    odds_home: Mapped[float | None] = mapped_column(Float, nullable=True)
    odds_draw: Mapped[float | None] = mapped_column(Float, nullable=True)
    odds_away: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    competition: Mapped[Competition] = relationship(back_populates="matches")
    home_team: Mapped[Team] = relationship(foreign_keys=[home_team_id])
    away_team: Mapped[Team] = relationship(foreign_keys=[away_team_id])
    predictions: Mapped[list[Prediction]] = relationship(back_populates="match")


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    match_id: Mapped[int] = mapped_column(
        ForeignKey("matches.id", ondelete="CASCADE"), nullable=False, index=True
    )
    model_name: Mapped[str] = mapped_column(String(64), nullable=False)
    # 'dixon_coles' | 'xgboost' | 'bayesian' | 'ensemble'

    # Match outcome
    prob_home: Mapped[float] = mapped_column(Float, nullable=False)
    prob_draw: Mapped[float] = mapped_column(Float, nullable=False)
    prob_away: Mapped[float] = mapped_column(Float, nullable=False)

    # Expected goals
    home_xg: Mapped[float] = mapped_column(Float, nullable=False)
    away_xg: Mapped[float] = mapped_column(Float, nullable=False)

    # Derived markets
    prob_btts: Mapped[float | None] = mapped_column(Float, nullable=True)
    prob_over_2_5: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Top scorelines as JSON: [{"home": 2, "away": 1, "prob": 0.114}, ...]
    scoreline_distribution: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)

    # Drivers as JSON: [{"label": "Rest advantage", "detail": "...", "impact_pp": 5.2}, ...]
    drivers: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)

    # Narrative (templated from drivers)
    narrative: Mapped[str | None] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    match: Mapped[Match] = relationship(back_populates="predictions")

    __table_args__ = (UniqueConstraint("match_id", "model_name", name="uq_pred_match_model"),)


class Insight(Base):
    __tablename__ = "insights"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    # 'player_streak' | 'team_form' | 'historic_record' | 'tactical_shift'

    subject: Mapped[str] = mapped_column(String(128), nullable=False)
    # Team or player name

    headline: Mapped[str] = mapped_column(String, nullable=False)
    detail: Mapped[str] = mapped_column(String, nullable=False)

    # Structured payload as JSON, e.g. {"games": 10, "shots_per": 4.2}
    data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # Higher = more notable
    notability: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # If the insight is fed into the model, false = context-only
    is_weighted: Mapped[bool] = mapped_column(Boolean, default=False)

    related_match_id: Mapped[int | None] = mapped_column(
        ForeignKey("matches.id", ondelete="SET NULL"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LeagueProjection(Base):
    __tablename__ = "league_projections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    competition_id: Mapped[int] = mapped_column(
        ForeignKey("competitions.id", ondelete="CASCADE"), nullable=False
    )
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)

    # Projected final position distribution
    expected_position: Mapped[float] = mapped_column(Float, nullable=False)
    expected_points: Mapped[float] = mapped_column(Float, nullable=False)
    title_probability: Mapped[float] = mapped_column(Float, default=0.0)
    top_four_probability: Mapped[float] = mapped_column(Float, default=0.0)
    relegation_probability: Mapped[float] = mapped_column(Float, default=0.0)

    # Position distribution as JSON: {"1": 0.42, "2": 0.31, ...}
    position_distribution: Mapped[dict] = mapped_column(JSON, default=dict)

    as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint("competition_id", "team_id", name="uq_proj_comp_team"),)


class BacktestRun(Base):
    __tablename__ = "backtest_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    model_name: Mapped[str] = mapped_column(String(64), nullable=False)
    season_start: Mapped[int] = mapped_column(Integer, nullable=False)
    season_end: Mapped[int] = mapped_column(Integer, nullable=False)

    n_predictions: Mapped[int] = mapped_column(Integer, nullable=False)
    brier_score: Mapped[float] = mapped_column(Float, nullable=False)
    log_loss: Mapped[float] = mapped_column(Float, nullable=False)
    top_pick_accuracy: Mapped[float] = mapped_column(Float, nullable=False)

    # Market benchmarks
    market_brier: Mapped[float | None] = mapped_column(Float, nullable=True)
    market_log_loss: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Calibration bins as JSON: [{"bin_lower": 0.0, "bin_upper": 0.1, "predicted": 0.05, "actual": 0.06, "count": 42}, ...]
    calibration_bins: Mapped[list[dict]] = mapped_column(JSON, default=list)

    # Simulated betting P&L (flat-staking, with disclaimer)
    simulated_pnl_units: Mapped[float | None] = mapped_column(Float, nullable=True)
    simulated_roi_pct: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
