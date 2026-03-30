"""Refresh MySQL pre-aggregated summary tables from the star schema."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.clients.mysql_client import connect_mysql


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SQL_TEAM_GAME = PROJECT_ROOT / "sql" / "mysql" / "003_populate_agg_team_game_totals.sql"
SQL_PLAYER_SEASON = PROJECT_ROOT / "sql" / "mysql" / "004_populate_agg_player_season_totals.sql"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Refresh MySQL summary tables from fact and dimension tables."
    )
    parser.add_argument(
        "--mode",
        choices=["full-refresh"],
        default="full-refresh",
        help="Refresh strategy. Currently full-refresh only.",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Print row counts after refresh.",
    )
    return parser.parse_args()


def read_sql(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def refresh_full(connection) -> None:
    team_game_sql = read_sql(SQL_TEAM_GAME)
    player_season_sql = read_sql(SQL_PLAYER_SEASON)

    cursor = connection.cursor()
    try:
        # Full rebuild is the safest choice here:
        # - reflects corrected fact rows
        # - removes stale summaries if source/facts changed
        # - simple and reproducible for coursework/demo
        connection.start_transaction()

        cursor.execute("DELETE FROM agg_team_game_totals")
        cursor.execute("DELETE FROM agg_player_season_totals")

        cursor.execute(team_game_sql)
        cursor.execute(player_season_sql)

        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()


def fetch_counts(connection) -> dict[str, int]:
    cursor = connection.cursor()
    try:
        counts = {}
        for table_name in ("agg_team_game_totals", "agg_player_season_totals"):
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            counts[table_name] = int(cursor.fetchone()[0])
        return counts
    finally:
        cursor.close()


def main() -> None:
    args = parse_args()
    connection = connect_mysql()
    try:
        if args.mode != "full-refresh":
            raise ValueError(f"Unsupported mode: {args.mode}")

        refresh_full(connection)

        if args.validate:
            print(json.dumps(fetch_counts(connection), indent=2, sort_keys=True))
    finally:
        connection.close()


if __name__ == "__main__":
    main()
