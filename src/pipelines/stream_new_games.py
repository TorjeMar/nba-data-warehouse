"""Incremental pipeline: discover new games, log raw payloads, and stream events."""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import pandas as pd

from src.etl.download_box_scores import FetchConfig, fetch_game_box_score
from src.etl.download_season import DEFAULT_SEASON_TYPES, fetch_games, season_slices
from src.etl.stream_contract import build_player_game_event
from src.etl.stream_producer import build_producer
from src.etl.transform import build_record


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Find new games after latest DB game ID, download box scores, log JSONL, and stream to Kafka.",
    )
    parser.add_argument(
        "--source-backend",
        choices=["mysql", "mongodb", "neo4j"],
        default="mysql",
        help="Backend used to determine the latest already-loaded game ID.",
    )
    parser.add_argument(
        "--incremental-mode",
        choices=["date", "id"],
        default="date",
        help="date: safer watermark+existence mode, id: faster max-game-id mode.",
    )
    parser.add_argument("--start-year", type=int, default=2024, help="Season start year to scan for new games.")
    parser.add_argument("--end-year", type=int, default=2026, help="Season end year to scan for new games.")
    parser.add_argument(
        "--season-cache-dir",
        default="data/season",
        help="Directory for cached season game listings (games_<season>_<type>.json).",
    )
    parser.add_argument(
        "--no-season-cache",
        action="store_true",
        help="Ignore local season cache and always query nba_api.",
    )
    parser.add_argument(
        "--lookback-years",
        type=int,
        default=1,
        help="In date mode, include this many years before watermark year for late arrivals.",
    )
    parser.add_argument(
        "--existence-check-batch-size",
        type=int,
        default=500,
        help="Batch size for DB existence checks in date mode.",
    )
    parser.add_argument("--season-types", nargs="*", default=list(DEFAULT_SEASON_TYPES))
    parser.add_argument("--topic", default="player-game-records", help="Kafka topic for produced events.")
    parser.add_argument("--broker", default="localhost:29092", help="Kafka bootstrap server.")
    parser.add_argument("--log-file", default="data/box_scores_incremental.jsonl", help="Append-only raw payload log file.")
    parser.add_argument("--producer-name", default="incremental-boxscore-producer")
    parser.add_argument("--producer-run-id", default=None)
    parser.add_argument("--max-new-games", type=int, default=None, help="Optional cap on number of new games to process.")
    parser.add_argument("--dry-run", action="store_true", help="Discover and list new game IDs without downloading/streaming.")

    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--max-timeout", type=int, default=45)
    parser.add_argument("--timeout-step", type=int, default=5)
    parser.add_argument("--max-retries", type=int, default=4)
    parser.add_argument("--invalid-retries", type=int, default=3)
    parser.add_argument("--max-backoff", type=float, default=30.0)
    parser.add_argument("--read-timeout-streak-limit", type=int, default=3)
    parser.add_argument("--max-elapsed", type=float, default=180.0)

    return parser.parse_args()


def connect_source_backend(source_backend: str) -> Any:
    if source_backend == "mysql":
        from src.clients.mysql_client import connect_mysql

        return connect_mysql()

    if source_backend == "mongodb":
        from src.clients.mongodb_client import connect_mongodb

        return connect_mongodb()

    if source_backend == "neo4j":
        from src.clients.neo4j_client import connect_neo4j

        return connect_neo4j()

    raise ValueError(f"Unsupported source backend: {source_backend}")


def close_source_backend(source_backend: str, resource: Any) -> None:
    if source_backend == "mysql":
        resource.close()
        return
    if source_backend == "mongodb":
        resource.client.close()
        return
    if source_backend == "neo4j":
        resource.close()
        return


def _parse_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return datetime.strptime(text[:10], "%Y-%m-%d").date()
        except ValueError:
            return None
    return None


def latest_loaded_game_date(source_backend: str, resource: Any) -> date | None:
    if source_backend == "mysql":
        cursor = resource.cursor()
        try:
            cursor.execute(
                """
                SELECT MAX(d.full_date)
                FROM dim_game g
                LEFT JOIN dim_date d ON d.date_key = g.game_date_key
                """
            )
            row = cursor.fetchone()
            return _parse_date(row[0]) if row and row[0] is not None else None
        finally:
            cursor.close()

    if source_backend == "mongodb":
        doc = resource.player_game_stats.find_one(
            filter={"gameDate": {"$ne": None}},
            projection={"_id": 0, "gameDate": 1},
            sort=[("gameDate", -1)],
        )
        if not doc:
            return None
        return _parse_date(doc.get("gameDate"))

    if source_backend == "neo4j":
        with resource.session() as session:
            result = session.run(
                """
                MATCH (:Game)-[:ON_DATE]->(d:Date)
                RETURN toString(max(d.fullDate)) AS latest_date
                """
            )
            record = result.single()
            if not record:
                return None
            return _parse_date(record.get("latest_date"))

    raise ValueError(f"Unsupported source backend: {source_backend}")


def latest_loaded_game_id(source_backend: str, resource: Any) -> str | None:
    if source_backend == "mysql":
        cursor = resource.cursor()
        try:
            cursor.execute("SELECT MAX(source_game_id) FROM dim_game")
            row = cursor.fetchone()
            return str(row[0]) if row and row[0] is not None else None
        finally:
            cursor.close()

    if source_backend == "mongodb":
        doc = resource.player_game_stats.find_one(
            filter={"sourceGameId": {"$exists": True}},
            projection={"_id": 0, "sourceGameId": 1},
            sort=[("sourceGameId", -1)],
        )
        if not doc:
            return None
        value = doc.get("sourceGameId")
        return str(value) if value is not None else None

    if source_backend == "neo4j":
        with resource.session() as session:
            result = session.run("MATCH (g:Game) RETURN max(g.sourceGameId) AS latest")
            record = result.single()
            if not record:
                return None
            value = record.get("latest")
            return str(value) if value is not None else None

    raise ValueError(f"Unsupported source backend: {source_backend}")


def infer_start_year_from_game_id(last_game_id: str | None, fallback: int, end_year: int) -> int:
    if not last_game_id or len(last_game_id) < 5:
        return min(fallback, end_year)
    yy = last_game_id[3:5]
    if not yy.isdigit():
        return min(fallback, end_year)
    guessed_year = 2000 + int(yy)
    return min(max(fallback, guessed_year), end_year)


def infer_start_year_from_watermark_date(
    watermark: date | None,
    fallback: int,
    end_year: int,
    lookback_years: int,
) -> int:
    if watermark is None:
        return min(fallback, end_year)
    adjusted = watermark.year - max(0, lookback_years - 1)
    return min(max(fallback, adjusted), end_year)


def discover_games_with_dates(start_year: int, end_year: int, season_types: list[str]) -> dict[str, date]:
    return discover_games_with_dates_from_source(
        start_year=start_year,
        end_year=end_year,
        season_types=season_types,
        season_cache_dir=None,
        no_season_cache=True,
    )


def _load_season_games_from_cache(season_cache_dir: Path, season_label: str, season_type: str) -> pd.DataFrame | None:
    suffix = season_type.replace(" ", "_")
    path = season_cache_dir / f"games_{season_label}_{suffix}.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, list) or not data:
        return pd.DataFrame()
    frame = pd.DataFrame(data)
    if "GAME_ID" not in frame.columns or "GAME_DATE" not in frame.columns:
        return pd.DataFrame()
    return frame


def discover_games_with_dates_from_source(
    *,
    start_year: int,
    end_year: int,
    season_types: list[str],
    season_cache_dir: str | None,
    no_season_cache: bool,
) -> dict[str, date]:
    games_with_dates: dict[str, date] = {}
    cache_dir = Path(season_cache_dir) if season_cache_dir else None
    for season_slice in season_slices(start_year, end_year, season_types=season_types):
        games = None
        if not no_season_cache and cache_dir is not None:
            games = _load_season_games_from_cache(cache_dir, season_slice.season_label, season_slice.season_type)
        if games is None:
            games = fetch_games(season_slice.season_label, season_slice.season_type)
        if games is None or games.empty:
            continue
        for _, row in games[["GAME_ID", "GAME_DATE"]].dropna().iterrows():
            game_id = str(row["GAME_ID"])
            game_date = _parse_date(row["GAME_DATE"])
            if game_date is None:
                continue
            games_with_dates[game_id] = game_date
    return games_with_dates


def find_existing_game_ids(
    source_backend: str,
    resource: Any,
    candidate_game_ids: list[str],
    batch_size: int,
) -> set[str]:
    if not candidate_game_ids:
        return set()

    def _chunks(values: list[str], size: int) -> list[list[str]]:
        return [values[i : i + size] for i in range(0, len(values), size)]

    if source_backend == "mysql":
        cursor = resource.cursor()
        try:
            found: set[str] = set()
            for batch in _chunks(candidate_game_ids, batch_size):
                placeholders = ",".join(["%s"] * len(batch))
                cursor.execute(
                    f"SELECT source_game_id FROM dim_game WHERE source_game_id IN ({placeholders})",
                    batch,
                )
                found.update(str(row[0]) for row in cursor.fetchall() if row and row[0] is not None)
            return found
        finally:
            cursor.close()

    if source_backend == "mongodb":
        found: set[str] = set()
        for batch in _chunks(candidate_game_ids, batch_size):
            docs = resource.player_game_stats.find(
                {"sourceGameId": {"$in": batch}},
                {"_id": 0, "sourceGameId": 1},
            )
            found.update(str(doc["sourceGameId"]) for doc in docs if doc.get("sourceGameId") is not None)
        return found

    if source_backend == "neo4j":
        with resource.session() as session:
            found: set[str] = set()
            for batch in _chunks(candidate_game_ids, batch_size):
                result = session.run(
                    """
                    UNWIND $ids AS id
                    MATCH (g:Game {sourceGameId: id})
                    RETURN g.sourceGameId AS source_game_id
                    """,
                    ids=batch,
                )
                found.update(str(record["source_game_id"]) for record in result if record.get("source_game_id") is not None)
            return found

    raise ValueError(f"Unsupported source backend: {source_backend}")


def select_new_game_ids(
    games_with_dates: dict[str, date],
    watermark_date: date | None,
    existing_game_ids: set[str],
    max_new_games: int | None,
) -> list[str]:
    selected: list[str] = []
    for game_id, game_date in sorted(games_with_dates.items(), key=lambda item: (item[1], item[0])):
        if watermark_date is not None and game_date <= watermark_date:
            continue
        if game_id in existing_game_ids:
            continue
        selected.append(game_id)

    if max_new_games is not None:
        return selected[:max_new_games]
    return selected


def iter_rows_from_column_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if not payload:
        return []
    sample = next(iter(payload.values()), None)
    if not isinstance(sample, dict):
        return []

    row_keys = sorted(sample.keys(), key=lambda value: int(value))
    rows: list[dict[str, Any]] = []
    for row_key in row_keys:
        row: dict[str, Any] = {}
        for column, values in payload.items():
            if isinstance(values, dict):
                row[column] = values.get(row_key)
            else:
                row[column] = values
        rows.append(row)
    return rows


def run_incremental_streaming(args: argparse.Namespace) -> dict[str, Any]:
    source_resource = connect_source_backend(args.source_backend)
    try:
        watermark_date = latest_loaded_game_date(args.source_backend, source_resource)
        latest_game_id = latest_loaded_game_id(args.source_backend, source_resource)
    finally:
        close_source_backend(args.source_backend, source_resource)

    if args.incremental_mode == "id":
        scan_start_year = infer_start_year_from_game_id(latest_game_id, args.start_year, args.end_year)
    else:
        scan_start_year = infer_start_year_from_watermark_date(
            watermark_date,
            args.start_year,
            args.end_year,
            args.lookback_years,
        )
    games_with_dates = discover_games_with_dates_from_source(
        start_year=scan_start_year,
        end_year=args.end_year,
        season_types=args.season_types,
        season_cache_dir=args.season_cache_dir,
        no_season_cache=args.no_season_cache,
    )
    discovered_game_ids = sorted(games_with_dates.keys())

    if args.incremental_mode == "id":
        existing_game_ids: set[str] = set()
        if latest_game_id is None:
            new_game_ids = discovered_game_ids
        else:
            new_game_ids = [game_id for game_id in discovered_game_ids if game_id > latest_game_id]
        if args.max_new_games is not None:
            new_game_ids = new_game_ids[: args.max_new_games]
    else:
        source_resource = connect_source_backend(args.source_backend)
        try:
            existing_game_ids = find_existing_game_ids(
                args.source_backend,
                source_resource,
                discovered_game_ids,
                args.existence_check_batch_size,
            )
        finally:
            close_source_backend(args.source_backend, source_resource)

        new_game_ids = select_new_game_ids(games_with_dates, watermark_date, existing_game_ids, args.max_new_games)

    if args.dry_run:
        return {
            "source_backend": args.source_backend,
            "incremental_mode": args.incremental_mode,
            "latest_game_id": latest_game_id,
            "watermark_date": watermark_date.isoformat() if watermark_date else None,
            "scan_start_year": scan_start_year,
            "discovered_games": len(discovered_game_ids),
            "already_loaded_candidates": len(existing_game_ids),
            "new_games": len(new_game_ids),
            "new_game_ids_preview": new_game_ids[:20],
            "dry_run": True,
        }

    fetch_cfg = FetchConfig(
        timeout=args.timeout,
        max_timeout=args.max_timeout,
        timeout_step=args.timeout_step,
        max_retries=args.max_retries,
        invalid_retries=args.invalid_retries,
        max_backoff=args.max_backoff,
        read_timeout_streak_limit=args.read_timeout_streak_limit,
        max_elapsed=args.max_elapsed,
    )

    producer = build_producer(args.broker)
    run_id = args.producer_run_id or str(uuid4())
    log_path = Path(args.log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    streamed_events = 0
    downloaded_games = 0
    failed_games: list[str] = []

    try:
        with log_path.open("a", encoding="utf-8") as log_handle:
            for game_id in new_game_ids:
                payload = fetch_game_box_score(game_id, fetch_cfg)
                if payload is None:
                    failed_games.append(game_id)
                    continue

                log_handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
                log_handle.flush()
                downloaded_games += 1

                rows = iter_rows_from_column_payload(payload)
                for source_line, row in enumerate(rows, start=1):
                    record = build_record(row)
                    event = build_player_game_event(
                        record,
                        source_file=str(log_path),
                        source_line=source_line,
                        producer_name=args.producer_name,
                        producer_run_id=run_id,
                    )
                    producer.send(args.topic, key=event["partition_key"], value=event).get(timeout=30)
                    streamed_events += 1
    finally:
        producer.flush()
        producer.close()

    return {
        "source_backend": args.source_backend,
        "incremental_mode": args.incremental_mode,
        "latest_game_id": latest_game_id,
        "watermark_date": watermark_date.isoformat() if watermark_date else None,
        "scan_start_year": scan_start_year,
        "discovered_games": len(discovered_game_ids),
        "already_loaded_candidates": len(existing_game_ids),
        "new_games": len(new_game_ids),
        "downloaded_games": downloaded_games,
        "failed_games": len(failed_games),
        "failed_game_ids": failed_games,
        "streamed_events": streamed_events,
        "topic": args.topic,
        "broker": args.broker,
        "log_file": str(log_path),
        "producer_run_id": run_id,
        "dry_run": False,
    }


def main() -> None:
    args = parse_args()
    result = run_incremental_streaming(args)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
