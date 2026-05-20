"""Understat scraper.

Pulls xG data for the top 5 leagues. No auth required but be polite —
add delays between requests in batch jobs.

Understat embeds match data as a JSON blob inside a `<script>` tag.
We parse that rather than hitting an API.
"""

from __future__ import annotations

import json
import re
from typing import Any

import httpx

BASE_URL = "https://understat.com"
SUPPORTED_LEAGUES = {"EPL", "La_liga", "Bundesliga", "Serie_A", "Ligue_1", "RFPL"}

# Understat encodes the JSON payload as a hex-escaped string assigned
# to a JS variable. This regex captures the value.
_DATA_RE = re.compile(r"JSON\.parse\('([^']+)'\)")


class UnderstatClient:
    def __init__(self, timeout: float = 30.0) -> None:
        self._client = httpx.AsyncClient(
            base_url=BASE_URL,
            timeout=timeout,
            headers={"User-Agent": "Mozilla/5.0 (research; the-final-third)"},
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> UnderstatClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def get_league_matches(self, league: str, season: int) -> list[dict]:
        """Return list of matches for a league-season with xG data.

        season is the starting year, e.g. 2024 for the 2024-25 season.
        """
        if league not in SUPPORTED_LEAGUES:
            raise ValueError(f"Unsupported league: {league}")
        r = await self._client.get(f"/league/{league}/{season}")
        r.raise_for_status()
        html = r.text

        matches_raw = self._extract_json_var(html, "datesData")
        if matches_raw is None:
            return []
        return matches_raw if isinstance(matches_raw, list) else []

    @staticmethod
    def _extract_json_var(html: str, var_name: str) -> Any:
        """Extract a JSON.parse('...') call by variable name from page HTML."""
        # Find var <name> = JSON.parse('...')
        pattern = re.compile(rf"var\s+{re.escape(var_name)}\s*=\s*JSON\.parse\('([^']+)'\)")
        m = pattern.search(html)
        if not m:
            return None
        encoded = m.group(1)
        # Understat uses \x escapes — decode by unescaping
        decoded = encoded.encode("utf-8").decode("unicode_escape")
        try:
            return json.loads(decoded)
        except json.JSONDecodeError:
            return None
