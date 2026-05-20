"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-21 00:00:00

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "competitions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(32), nullable=False, unique=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("tier", sa.String(32), nullable=False, server_default="LEAGUE"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "teams",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("short_name", sa.String(64), nullable=False),
        sa.Column("full_name", sa.String(128), nullable=False),
        sa.Column("tla", sa.String(8), nullable=True),
        sa.Column("crest_url", sa.String(512), nullable=True),
        sa.Column("primary_color", sa.String(16), nullable=True),
        sa.Column("secondary_color", sa.String(16), nullable=True),
        sa.Column("is_premier_league", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("short_name", name="uq_team_short_name"),
    )

    op.create_table(
        "matches",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("external_id", sa.String(64), nullable=True, unique=True),
        sa.Column(
            "competition_id",
            sa.Integer(),
            sa.ForeignKey("competitions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "home_team_id",
            sa.Integer(),
            sa.ForeignKey("teams.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "away_team_id",
            sa.Integer(),
            sa.ForeignKey("teams.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("kickoff", sa.DateTime(timezone=True), nullable=False),
        sa.Column("matchday", sa.Integer(), nullable=True),
        sa.Column("venue", sa.String(128), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="SCHEDULED"),
        sa.Column("home_score", sa.Integer(), nullable=True),
        sa.Column("away_score", sa.Integer(), nullable=True),
        sa.Column("home_xg", sa.Float(), nullable=True),
        sa.Column("away_xg", sa.Float(), nullable=True),
        sa.Column("odds_home", sa.Float(), nullable=True),
        sa.Column("odds_draw", sa.Float(), nullable=True),
        sa.Column("odds_away", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_matches_kickoff", "matches", ["kickoff"])

    op.create_table(
        "predictions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "match_id",
            sa.Integer(),
            sa.ForeignKey("matches.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("model_name", sa.String(64), nullable=False),
        sa.Column("prob_home", sa.Float(), nullable=False),
        sa.Column("prob_draw", sa.Float(), nullable=False),
        sa.Column("prob_away", sa.Float(), nullable=False),
        sa.Column("home_xg", sa.Float(), nullable=False),
        sa.Column("away_xg", sa.Float(), nullable=False),
        sa.Column("prob_btts", sa.Float(), nullable=True),
        sa.Column("prob_over_2_5", sa.Float(), nullable=True),
        sa.Column("scoreline_distribution", sa.JSON(), nullable=True),
        sa.Column("drivers", sa.JSON(), nullable=True),
        sa.Column("narrative", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("match_id", "model_name", name="uq_pred_match_model"),
    )
    op.create_index("ix_predictions_match_id", "predictions", ["match_id"])

    op.create_table(
        "insights",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("kind", sa.String(64), nullable=False),
        sa.Column("subject", sa.String(128), nullable=False),
        sa.Column("headline", sa.String(), nullable=False),
        sa.Column("detail", sa.String(), nullable=False),
        sa.Column("data", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("notability", sa.Float(), nullable=False, server_default="0"),
        sa.Column("is_weighted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "related_match_id",
            sa.Integer(),
            sa.ForeignKey("matches.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "league_projections",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "competition_id",
            sa.Integer(),
            sa.ForeignKey("competitions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "team_id",
            sa.Integer(),
            sa.ForeignKey("teams.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("expected_position", sa.Float(), nullable=False),
        sa.Column("expected_points", sa.Float(), nullable=False),
        sa.Column("title_probability", sa.Float(), nullable=False, server_default="0"),
        sa.Column("top_four_probability", sa.Float(), nullable=False, server_default="0"),
        sa.Column("relegation_probability", sa.Float(), nullable=False, server_default="0"),
        sa.Column("position_distribution", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column(
            "as_of",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("competition_id", "team_id", name="uq_proj_comp_team"),
    )

    op.create_table(
        "backtest_runs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("model_name", sa.String(64), nullable=False),
        sa.Column("season_start", sa.Integer(), nullable=False),
        sa.Column("season_end", sa.Integer(), nullable=False),
        sa.Column("n_predictions", sa.Integer(), nullable=False),
        sa.Column("brier_score", sa.Float(), nullable=False),
        sa.Column("log_loss", sa.Float(), nullable=False),
        sa.Column("top_pick_accuracy", sa.Float(), nullable=False),
        sa.Column("market_brier", sa.Float(), nullable=True),
        sa.Column("market_log_loss", sa.Float(), nullable=True),
        sa.Column("calibration_bins", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("simulated_pnl_units", sa.Float(), nullable=True),
        sa.Column("simulated_roi_pct", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("backtest_runs")
    op.drop_table("league_projections")
    op.drop_table("insights")
    op.drop_index("ix_predictions_match_id", table_name="predictions")
    op.drop_table("predictions")
    op.drop_index("ix_matches_kickoff", table_name="matches")
    op.drop_table("matches")
    op.drop_table("teams")
    op.drop_table("competitions")
