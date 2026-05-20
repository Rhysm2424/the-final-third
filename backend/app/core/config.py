"""Application configuration loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed configuration. Loaded once and cached."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    database_url: str = Field(default="postgresql+asyncpg://postgres:postgres@db:5432/finalthird")

    # Demo mode
    demo_mode: bool = Field(default=True)

    # External data sources (only required when demo_mode is False)
    football_data_api_key: str = Field(default="")
    rapidapi_key: str = Field(default="")

    # Sentry
    sentry_dsn_backend: str = Field(default="")

    # CORS
    cors_origins: str = Field(default="http://localhost:3000")

    # Logging
    log_level: str = Field(default="INFO")

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
