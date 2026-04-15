import json
from pathlib import Path
from datetime import datetime
from typing import Any

from src.etl.download_season import download_season


def load_season(season_label: str, season_type: str) -> list[dict]:
    filename = f"{season_label}_{season_type.replace(' ', '_')}.json"
    path = Path("data/season") / f"games_{filename}"

    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        pass
    except json.JSONDecodeError as exc:
        print(f"Error decoding JSON for {season_label} | {season_type}: {exc}. Returning empty list.")
        return []
    except Exception as exc:
        print(f"Unexpected error loading {season_label} | {season_type}: {exc}. Returning empty list.")
        return []

    try:
        download_season(
            season_label=season_label,
            season_types=[season_type],
            output_dir="data/season",
            skip_existing=True,
        )
    except Exception as exc:
        print(f"Error downloading season data for {season_label} | {season_type}: {exc}. Returning empty list.")
        return []

    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Downloaded file still missing for {season_label} | {season_type}. Returning empty list.")
        return []
    except json.JSONDecodeError as exc:
        print(f"Downloaded file invalid JSON for {season_label} | {season_type}: {exc}. Returning empty list.")
        return []
    except Exception as exc:
        print(f"Unexpected error after download for {season_label} | {season_type}: {exc}. Returning empty list.")
        return []


def load_all_seasons(season_labels: list[str], season_types: list[str]) -> dict[str, list[dict]]:
    all_data: dict[str, list[dict]] = {}
    for season_label in season_labels:
        for season_type in season_types:
            key = f"{season_label}_{season_type}"
            rows = load_season(season_label, season_type)
            enriched_rows = []
            for row in rows:
                enriched = dict(row)
                enriched["SEASON_LABEL"] = season_label
                enriched["SEASON_TYPE"] = season_type
                enriched_rows.append(enriched)
            all_data[key] = enriched_rows
    return all_data

def build_games_dict(season_labels: list[str], season_types: list[str]) -> dict[str, list[dict]]:
    """Build a dictionary keyed by GAME_ID with one entry per team perspective."""
    all_seasons_data = load_all_seasons(season_labels, season_types)
    games_dict: dict[str, list[dict]] = {}
    for games in all_seasons_data.values():
        for game in games:
            game_id = str(game.get("GAME_ID", ""))
            if not game_id:
                continue
            games_dict.setdefault(game_id, []).append(game)
    return games_dict


def get_team_game_metadata(
    game_id: str,
    team_id: int,
    games_dict: dict[str, list[dict]],
) -> dict[str, Any]:
    """Return the game metadata row matching a specific team in a game."""
    rows = games_dict.get(game_id, [])
    if not rows:
        return {}

    for row in rows:
        try:
            if int(row.get("TEAM_ID")) == team_id:
                return row
        except (TypeError, ValueError):
            continue

    # Fallback: keep pipeline robust even if TEAM_ID is missing.
    return rows[0]

# get game date from loaded game metadata rows, if available, otherwise return None
def get_game_date(row: dict) -> datetime | None:
    value = row.get("GAME_DATE")

    if value is None and isinstance(row.get("game_metadata"), dict):
        value = row["game_metadata"].get("GAME_DATE")

    if not isinstance(value, str):
        return None

    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        print(f"Warning: invalid GAME_DATE format {value!r}, expected YYYY-MM-DD. Error: {exc}")
        return None


def get_game_season(row: dict) -> str | None:
    season_label = row.get("SEASON_LABEL")
    if season_label is None and isinstance(row.get("game_metadata"), dict):
        season_label = row["game_metadata"].get("SEASON_LABEL")
    if isinstance(season_label, str):
        normalized = season_label.strip()
        if normalized:
            return normalized

    game_date = get_game_date(row)
    if game_date is None:
        return None

    year = game_date.year
    month = game_date.month

    if month >= 10:  # October or later means season starts in this year
        return f"{year}-{str(year + 1)[-2:]}"
    return f"{year - 1}-{str(year)[-2:]}"


def get_game_type(row: dict) -> str | None:
    season_type = row.get("SEASON_TYPE")
    if season_type is None and isinstance(row.get("game_metadata"), dict):
        season_type = row["game_metadata"].get("SEASON_TYPE")

    if not isinstance(season_type, str):
        return None

    normalized = season_type.strip().lower()
    game_type_map = {
        "regular season": "regular_season",
        "playoffs": "playoffs",
        "pre season": "preseason",
        "all star": "all_star",
        "playin": "play_in",
    }
    return game_type_map.get(normalized)

def get_matchup_type(row: dict) -> str | None:
    matchup = row.get("MATCHUP")
    if not isinstance(matchup, str):
        return None
    normalized = " ".join(matchup.split())
    return normalized or None


def get_home_or_away(row: dict) -> str | None:
    matchup = get_matchup_type(row)
    if matchup is None:
        return None
    if "vs." in matchup:
        return "home"
    if "@" in matchup:
        return "away"
    return None


_GAMES_DICT = build_games_dict(
    [f"{year}-{str(year + 1)[-2:]}" for year in range(2000, 2026)],
    ["Regular Season", "Playoffs", "Pre Season", "All Star", "PlayIn"],
)
