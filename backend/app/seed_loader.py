"""Seed loader.

Runs automatically at container start. If DEMO_MODE is true and the
database is empty, populates it with the bundled demo dataset so the
site renders on first boot.

Once real data flows in (DEMO_MODE=false + ingestion), this script
exits without touching anything.
"""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import select

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.db import AsyncSessionLocal
from app.db.models import (
    BacktestRun,
    Competition,
    Insight,
    LeagueProjection,
    Match,
    Prediction,
    Team,
)
from app.features.drivers import build_drivers
from app.features.narrative import generate_narrative
from app.models import DixonColesModel

SEED_PATH = Path(__file__).parent.parent / "seed" / "demo_data.json"


async def run() -> int:
    configure_logging()
    log = get_logger(__name__)
    settings = get_settings()

    if not settings.demo_mode:
        log.info("seed.skip_live_mode")
        return 0

    async with AsyncSessionLocal() as db:
        # Idempotent: only seed if empty
        existing = (await db.execute(select(Team).limit(1))).first()
        if existing:
            log.info("seed.already_populated")
            return 0

        data = json.loads(SEED_PATH.read_text())

        # Competitions
        comp_map: dict[str, Competition] = {}
        for c in data["competitions"]:
            comp = Competition(code=c["code"], name=c["name"], tier=c["tier"])
            db.add(comp)
            comp_map[c["code"]] = comp
        await db.flush()

        # Teams
        team_map: dict[str, Team] = {}
        for t in data["teams"]:
            team = Team(
                short_name=t["short_name"],
                full_name=t["full_name"],
                tla=t["tla"],
                primary_color=t["primary_color"],
                secondary_color=t["secondary_color"],
                is_premier_league=t["is_premier_league"],
            )
            db.add(team)
            team_map[t["short_name"]] = team
        await db.flush()

        # Historical matches (with results)
        now = datetime.now(UTC).replace(hour=15, minute=0, second=0, microsecond=0)
        historical_matches: list[Match] = []
        for h in data["historical_offset_days"]:
            kickoff = now + timedelta(days=h["offset"])
            m = Match(
                competition_id=comp_map[h["competition"]].id,
                home_team_id=team_map[h["home"]].id,
                away_team_id=team_map[h["away"]].id,
                kickoff=kickoff,
                matchday=h.get("matchday"),
                status="FINISHED",
                home_score=h["home_score"],
                away_score=h["away_score"],
                odds_home=h.get("odds_home"),
                odds_draw=h.get("odds_draw"),
                odds_away=h.get("odds_away"),
            )
            db.add(m)
            historical_matches.append(m)

        # Upcoming fixtures
        upcoming_matches: list[Match] = []
        for f in data["fixtures_offset_days"]:
            kickoff = (now + timedelta(days=f["offset"])).replace(
                hour=f["hour"], minute=f["minute"]
            )
            m = Match(
                competition_id=comp_map[f["competition"]].id,
                home_team_id=team_map[f["home"]].id,
                away_team_id=team_map[f["away"]].id,
                kickoff=kickoff,
                matchday=f.get("matchday"),
                venue=f.get("venue"),
                status=f["status"],
            )
            db.add(m)
            upcoming_matches.append(m)

        await db.flush()

        # Train Dixon-Coles on the historical seed and predict the upcoming fixtures
        import pandas as pd

        history_rows = [
            {
                "home_team": team_map_inv(team_map, m.home_team_id),
                "away_team": team_map_inv(team_map, m.away_team_id),
                "home_score": m.home_score,
                "away_score": m.away_score,
                "date": m.kickoff,
            }
            for m in historical_matches
        ]
        df = pd.DataFrame(history_rows)

        model = DixonColesModel()
        try:
            model.fit(df)
        except Exception as e:
            log.warning("seed.model_fit_failed", error=str(e))
            model = None

        if model is not None and model.is_fitted:
            for m in upcoming_matches:
                home_name = team_map_inv(team_map, m.home_team_id)
                away_name = team_map_inv(team_map, m.away_team_id)
                try:
                    pred = model.predict_match(home_name, away_name)
                except Exception:
                    continue
                drivers = build_drivers(home_name, away_name, pred, df)
                narrative = generate_narrative(home_name, away_name, pred, drivers)
                db.add(
                    Prediction(
                        match_id=m.id,
                        model_name="ensemble",
                        prob_home=pred.prob_home,
                        prob_draw=pred.prob_draw,
                        prob_away=pred.prob_away,
                        home_xg=pred.home_xg,
                        away_xg=pred.away_xg,
                        prob_btts=pred.prob_btts,
                        prob_over_2_5=pred.prob_over_2_5,
                        scoreline_distribution=pred.scoreline_distribution,
                        drivers=drivers,
                        narrative=narrative,
                    )
                )

            # Predictions for the finished historical matches too — used by
            # the Track Record "recent" list.
            for m in historical_matches:
                home_name = team_map_inv(team_map, m.home_team_id)
                away_name = team_map_inv(team_map, m.away_team_id)
                try:
                    pred = model.predict_match(home_name, away_name)
                except Exception:
                    continue
                db.add(
                    Prediction(
                        match_id=m.id,
                        model_name="ensemble",
                        prob_home=pred.prob_home,
                        prob_draw=pred.prob_draw,
                        prob_away=pred.prob_away,
                        home_xg=pred.home_xg,
                        away_xg=pred.away_xg,
                        prob_btts=pred.prob_btts,
                        prob_over_2_5=pred.prob_over_2_5,
                    )
                )

        # Insights
        for ins in data["insights"]:
            db.add(
                Insight(
                    kind=ins["kind"],
                    subject=ins["subject"],
                    headline=ins["headline"],
                    detail=ins["detail"],
                    data=ins["data"],
                    notability=ins["notability"],
                    is_weighted=ins["is_weighted"],
                )
            )

        # League projections
        pl_id = comp_map["PL"].id
        for proj in data["league_projections"]:
            team = team_map.get(proj["team"])
            if not team:
                continue
            db.add(
                LeagueProjection(
                    competition_id=pl_id,
                    team_id=team.id,
                    expected_position=proj["expected_position"],
                    expected_points=proj["expected_points"],
                    title_probability=proj["title_probability"],
                    top_four_probability=proj["top_four_probability"],
                    relegation_probability=proj["relegation_probability"],
                    position_distribution={},
                )
            )

        # Backtest
        bt = data["backtest"]
        db.add(
            BacktestRun(
                model_name=bt["model_name"],
                season_start=bt["season_start"],
                season_end=bt["season_end"],
                n_predictions=bt["n_predictions"],
                brier_score=bt["brier_score"],
                log_loss=bt["log_loss"],
                top_pick_accuracy=bt["top_pick_accuracy"],
                market_brier=bt["market_brier"],
                market_log_loss=bt["market_log_loss"],
                calibration_bins=bt["calibration_bins"],
                simulated_pnl_units=bt["simulated_pnl_units"],
                simulated_roi_pct=bt["simulated_roi_pct"],
            )
        )

        await db.commit()
        log.info(
            "seed.done",
            teams=len(team_map),
            competitions=len(comp_map),
            historical=len(historical_matches),
            upcoming=len(upcoming_matches),
        )

    return 0


def team_map_inv(team_map: dict[str, Team], team_id: int) -> str:
    for name, team in team_map.items():
        if team.id == team_id:
            return name
    return "Unknown"


if __name__ == "__main__":
    sys.exit(asyncio.run(run()))
