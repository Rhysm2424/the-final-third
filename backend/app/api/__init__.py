"""FastAPI route handlers."""

from fastapi import APIRouter

from app.api.routes import fixtures, health, insights, league, matches, track_record

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(fixtures.router, prefix="/fixtures", tags=["fixtures"])
api_router.include_router(matches.router, prefix="/matches", tags=["matches"])
api_router.include_router(insights.router, prefix="/insights", tags=["insights"])
api_router.include_router(league.router, prefix="/league", tags=["league"])
api_router.include_router(track_record.router, prefix="/track-record", tags=["track-record"])
