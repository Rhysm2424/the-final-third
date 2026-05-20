"""Data ingestion clients — football-data.org, API-Football, Understat, Football-Data.co.uk."""

from app.ingestion.api_football_client import APIFootballClient
from app.ingestion.fbcouk_client import FootballDataCoUKClient
from app.ingestion.football_data_client import FootballDataOrgClient
from app.ingestion.understat_client import UnderstatClient

__all__ = [
    "APIFootballClient",
    "FootballDataCoUKClient",
    "FootballDataOrgClient",
    "UnderstatClient",
]
