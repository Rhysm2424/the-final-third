"""API-Football client via RapidAPI.

Free tier: 100 requests/day. Use sparingly — best for pre-match
lineups and odds.
"""

from __future__ import annotations

from typing import Any

import httpx

BASE_URL = "https://api-football-v1.p.rapidapi.com/v3"


class APIFootballClient:
    def __init__(self, api_key: str, timeout: float = 30.0) -> None:
        if not api_key:
            raise ValueError("APIFootballClient requires an API key")
        self._client = httpx.AsyncClient(
            base_url=BASE_URL,
            headers={
                "x-rapidapi-key": api_key,
                "x-rapidapi-host": "api-football-v1.p.rapidapi.com",
            },
            timeout=timeout,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> APIFootballClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def get_fixtures(
        self,
        league: int,
        season: int,
        date: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"league": league, "season": season}
        if date is not None:
            params["date"] = date
        r = await self._client.get("/fixtures", params=params)
        r.raise_for_status()
        data: dict[str, Any] = r.json()
        return data

    async def get_lineups(self, fixture_id: int) -> dict[str, Any]:
        r = await self._client.get("/fixtures/lineups", params={"fixture": fixture_id})
        r.raise_for_status()
        data: dict[str, Any] = r.json()
        return data

    async def get_odds(self, fixture_id: int) -> dict[str, Any]:
        r = await self._client.get("/odds", params={"fixture": fixture_id})
        r.raise_for_status()
        data: dict[str, Any] = r.json()
        return data
