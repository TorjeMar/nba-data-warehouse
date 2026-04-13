"""Download NBA season metadata (game listings per season slice)."""

from __future__ import annotations

import argparse
import json
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from nba_api.stats.endpoints import leaguegamefinder
from requests.exceptions import RequestException


DEFAULT_SEASON_TYPES = ("Regular Season", "Playoffs", "Pre Season", "All Star", "PlayIn")


@dataclass(frozen=True, slots=True)
class SeasonSlice:
    season_label: str
    season_type: str


def season_label_from_start_year(start_year: int) -> str:
    end_year_two_digits = (start_year + 1) % 100
    return f"{start_year}-{end_year_two_digits:02d}"


def season_slices(
    start_year: int,
    end_year: int,
    season_types: Iterable[str] = DEFAULT_SEASON_TYPES,
) -> Iterable[SeasonSlice]:
    for year in range(start_year, end_year + 1):
        label = season_label_from_start_year(year)
        for season_type in season_types:
            yield SeasonSlice(season_label=label, season_type=season_type)


def fetch_games(
    season_label: str,
    season_type: str,
    *,
    timeout_seconds: int = 90,
    max_retries: int = 6,
    backoff_seconds: float = 2.0,
) -> Any | None:
    for attempt in range(1, max_retries + 1):
        try:
            effective_timeout = timeout_seconds + (attempt - 1) * 15
            finder = leaguegamefinder.LeagueGameFinder(
                season_nullable=season_label,
                season_type_nullable=season_type,
                timeout=effective_timeout,
            )
            return finder.get_data_frames()[0]
        except RequestException as exc:
            if attempt == max_retries:
                print(
                    f"  Failed after {max_retries} attempts for "
                    f"{season_label} | {season_type}: {exc}"
                )
                return None

            wait = backoff_seconds * (2 ** (attempt - 1)) + random.uniform(0.2, 1.0)
            print(
                f"  Request failed (attempt {attempt}/{max_retries}) for "
                f"{season_label} | {season_type}: {exc}"
            )
            print(f"  Retrying in {wait:.1f}s...")
            time.sleep(wait)

    return None


def _output_path(output_dir: Path, season_label: str, season_type: str) -> Path:
    suffix = season_type.replace(" ", "_")
    return output_dir / f"games_{season_label}_{suffix}.json"


def show_games(
    start_year: int = 2000,
    end_year: int = 2024,
    output_dir: str = "data/season",
    season_types: Iterable[str] = DEFAULT_SEASON_TYPES,
    skip_existing: bool = True,
    pause_between_calls_seconds: float = 1.5,
) -> None:
    """Fetch and persist season game listing files."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    all_slices = list(season_slices(start_year, end_year, season_types=season_types))
    if skip_existing:
        all_slices = [
            s for s in all_slices
            if not _output_path(out_dir, s.season_label, s.season_type).exists()
        ]

    if not all_slices:
        print(f"All requested season files already exist in {out_dir}.")
        return

    for slice_ in all_slices:
        print(f"Processing {slice_.season_label} | {slice_.season_type}...")
        target_file = _output_path(out_dir, slice_.season_label, slice_.season_type)

        games = fetch_games(slice_.season_label, slice_.season_type)

        if games is None:
            print("  Skipping after repeated request failures.")
            time.sleep(pause_between_calls_seconds)
            print()
            continue

        if games.empty:
            print("  No games returned.")
            with target_file.open("w", encoding="utf-8") as f:
                json.dump([], f, indent=2)
            print(f"  Saved empty file: {target_file}")
            time.sleep(pause_between_calls_seconds)
            continue

        unique_game_count = games["GAME_ID"].nunique()
        print(f"  Rows: {len(games)} | Unique games: {unique_game_count}")

        columns_to_show = ["GAME_ID", "GAME_DATE", "TEAM_ID", "TEAM_ABBREVIATION", "MATCHUP"]
        available_columns = [c for c in columns_to_show if c in games.columns]

        with target_file.open("w", encoding="utf-8") as f:
            json.dump(games[available_columns].to_dict(orient="records"), f, indent=2)

        print(f"  Saved: {target_file}")
        time.sleep(pause_between_calls_seconds)
        print()


def download_season(
    season_label: str,
    output_dir: str = "data/season",
    season_types: Iterable[str] = DEFAULT_SEASON_TYPES,
    skip_existing: bool = True,
) -> None:
    show_games(
        start_year=int(season_label[:4]),
        end_year=int(season_label[:4]),
        output_dir=output_dir,
        season_types=season_types,
        skip_existing=skip_existing,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Download NBA season game listings.")
    parser.add_argument("--start-year", type=int, default=2000)
    parser.add_argument("--end-year", type=int, default=2025)
    parser.add_argument("--season-label", type=str, default=None, help="Single season label like 2023-24.")
    parser.add_argument("--output-dir", type=str, default="data/season")
    parser.add_argument("--season-types", nargs="*", default=list(DEFAULT_SEASON_TYPES))
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--pause-between-calls-seconds", type=float, default=1.5)

    args = parser.parse_args()

    if args.season_label:
        download_season(
            season_label=args.season_label,
            output_dir=args.output_dir,
            season_types=args.season_types,
            skip_existing=args.skip_existing,
        )
        return

    show_games(
        start_year=args.start_year,
        end_year=args.end_year,
        output_dir=args.output_dir,
        season_types=args.season_types,
        skip_existing=args.skip_existing,
        pause_between_calls_seconds=args.pause_between_calls_seconds,
    )


if __name__ == "__main__":
    main()
