"""League table projections."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import (
    CompetitionOut,
    LeagueProjectionResponse,
    LeagueProjectionRow,
    TeamOut,
)
from app.db import get_db
from app.db.models import Competition, LeagueProjection, Team

router = APIRouter()


@router.get("/{code}", response_model=LeagueProjectionResponse)
async def get_league_projections(
    code: str, db: AsyncSession = Depends(get_db)
) -> LeagueProjectionResponse:
    comp_stmt = select(Competition).where(Competition.code == code)
    comp = (await db.execute(comp_stmt)).scalar_one_or_none()
    if not comp:
        raise HTTPException(status_code=404, detail="Competition not found")

    # LeagueProjection has no ORM relationship to Team in the model, so we
    # fetch projections and teams separately and join in Python.
    proj_stmt = (
        select(LeagueProjection)
        .where(LeagueProjection.competition_id == comp.id)
        .order_by(LeagueProjection.expected_position.asc())
    )
    projections = (await db.execute(proj_stmt)).scalars().all()

    if not projections:
        # Empty projection set is valid — return empty rows
        return LeagueProjectionResponse(
            competition=CompetitionOut.model_validate(comp),
            as_of=comp.created_at,
            rows=[],
        )

    team_ids = [p.team_id for p in projections]
    teams = (await db.execute(select(Team).where(Team.id.in_(team_ids)))).scalars().all()
    team_map = {t.id: t for t in teams}

    rows = [
        LeagueProjectionRow(
            team=TeamOut.model_validate(team_map[p.team_id]),
            expected_position=p.expected_position,
            expected_points=p.expected_points,
            title_probability=p.title_probability,
            top_four_probability=p.top_four_probability,
            relegation_probability=p.relegation_probability,
        )
        for p in projections
        if p.team_id in team_map
    ]

    as_of = max((p.as_of for p in projections), default=comp.created_at)

    return LeagueProjectionResponse(
        competition=CompetitionOut.model_validate(comp),
        as_of=as_of,
        rows=rows,
    )
