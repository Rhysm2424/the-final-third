"""football-data.org API client.

Free tier covers the major European leagues including the Premier League
and Champions League. Rate-limited to 10 requests / minute.
"""

from __future__ import annotations

from typing import Any

import httpx

from app.core.logging import get_logger

log = get_logger(__name__)

BASE_URL = "https://api.football-data.org/v4"


class FootballDataOrgClient:
    def __init__(self, api_key: str, timeout: float = 30.0) -> None:
        if not api_key:
            raise ValueError("FootballDataOrgClient requires an API key")
        self._client = httpx.AsyncClient(
            base_url=BASE_URL,
            headers={"X-Auth-Token": api_key},
            timeout=timeout,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> FootballDataOrgClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def get_competition(self, code: str) -> dict[str, Any]:
        r = await self._client.get(f"/competitions/{code}")
        r.raise_for_status()
        data: dict[str, Any] = r.json()
        return data

    async def get_competition_matches(
        self,
        code: str,
        season: int | None = None,
        status: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if season is not None:
            params["season"] = season
        if status is not None:
            params["status"] = status
        if date_from is not None:
            params["dateFrom"] = date_from
        if date_to is not None:
            params["dateTo"] = date_to
        r = await self._client.get(f"/competitions/{code}/matches", params=params)
        r.raise_for_status()
        data: dict[str, Any] = r.json()
        return data

    async def get_competition_teams(self, code: str) -> dict[str, Any]:
        r = await self._client.get(f"/competitions/{code}/teams")
        r.raise_for_status()
        data: dict[str, Any] = r.json()
        return data

    async def get_competition_standings(self, code: str) -> dict[str, Any]:
        r = await self._client.get(f"/competitions/{code}/standings")
        r.raise_for_status()
        data: dict[str, Any] = r.json()
        return data
