"""FastAPI application entrypoint."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from app import __version__
from app.api import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger

settings = get_settings()


def _init_sentry() -> None:
    if not settings.sentry_dsn_backend:
        return
    sentry_sdk.init(
        dsn=settings.sentry_dsn_backend,
        integrations=[FastApiIntegration(), SqlalchemyIntegration()],
        traces_sample_rate=0.1,
        send_default_pii=False,
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    _init_sentry()
    log = get_logger(__name__)
    log.info("startup", version=__version__, demo_mode=settings.demo_mode)
    yield
    log.info("shutdown")


app = FastAPI(
    title="The Final Third — API",
    version=__version__,
    description="Football match prediction API.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(api_router)
