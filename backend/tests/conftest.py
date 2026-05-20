"""pytest configuration."""

from __future__ import annotations

import os

# Use a separate test database URL if available
os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/finalthird_test"
)
os.environ.setdefault("DEMO_MODE", "true")
os.environ.setdefault("LOG_LEVEL", "WARNING")
