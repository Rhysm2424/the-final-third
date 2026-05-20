"""Insights feed — auto-mined statistical patterns."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import InsightOut
from app.db import get_db
from app.db.models import Insight

router = APIRouter()


@router.get("", response_model=list[InsightOut])
async def list_insights(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
) -> list[InsightOut]:
    stmt = (
        select(Insight).order_by(Insight.notability.desc(), Insight.created_at.desc()).limit(limit)
    )
    result = await db.execute(stmt)
    return [InsightOut.model_validate(i) for i in result.scalars().all()]
