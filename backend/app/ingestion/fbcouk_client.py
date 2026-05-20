"""Football-Data.co.uk client.

Static CSV files with 30+ years of historical results and closing odds
from multiple bookmakers. Essential for backtesting.

URL pattern: https://www.football-data.co.uk/mmz4281/<season>/<league>.csv
where season is e.g. "2425" for the 2024-25 season and league is "E0"
for the Premier League.
"""

from __future__ import annotations

from io import StringIO
from typing import Any

import httpx
import pandas as pd

BASE_URL = "https://www.football-data.co.uk/mmz4281"

LEAGUE_CODES = {
    "premier_league": "E0",
    "championship": "E1",
    "league_one": "E2",
    "league_two": "E3",
    "national": "EC",
    "scottish_premier": "SC0",
    "bundesliga": "D1",
    "la_liga": "SP1",
    "serie_a": "I1",
    "ligue_1": "F1",
}


class FootballDataCoUKClient:
    def __init__(self, timeout: float = 60.0) -> None:
        self._client = httpx.AsyncClient(timeout=timeout)

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> FootballDataCoUKClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def get_season(self, league: str, season_start_year: int) -> pd.DataFrame:
        """Fetch a season as a pandas DataFrame.

        season_start_year is the year the season started, e.g. 2024 for 2024-25.
        Returns empty DataFrame if the season isn't yet available.
        """
        league_code = LEAGUE_CODES.get(league)
        if not league_code:
            raise ValueError(f"Unknown league: {league}")
        season_str = f"{str(season_start_year)[-2:]}{str(season_start_year + 1)[-2:]}"
        url = f"{BASE_URL}/{season_str}/{league_code}.csv"
        r = await self._client.get(url)
        if r.status_code == 404:
            return pd.DataFrame()
        r.raise_for_status()
        return pd.read_csv(StringIO(r.text))
