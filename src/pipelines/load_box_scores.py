"""CLI entry point for loading box score warehouse data."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.etl.transform import chunked, iter_records, summarize_records


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load box score records into warehouse backends.")
    parser.add_argument(
        "--backend",
        choices=["mysql", "mongodb", "neo4j", "all"],
        required=True,
        help="Target backend to load.",
    )
    parser.add_argument(
        "--input",
        default="data/box_scores.jsonl",
        help="Path to the source box score JSONL file.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Number of player records to transform per batch.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional record limit for smoke tests.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Transform data and print a summary without writing to a backend.",
    )
    return parser.parse_args()


def dry_run_summary(input_path: str, limit: int | None) -> None:
    summary = summarize_records(iter_records(input_path, limit=limit))
    print(json.dumps(summary, indent=2, sort_keys=True))


def load_mysql(input_path: str, batch_size: int, limit: int | None) -> int:
    from src.clients.mysql_client import connect_mysql
    from src.etl.load_mysql import load_mysql_records

    loaded = 0
    connection = connect_mysql()
    try:
        for batch in chunked(iter_records(input_path, limit=limit), batch_size):
            loaded += load_mysql_records(connection, batch)
    finally:
        connection.close()
    return loaded


def load_mongodb(input_path: str, batch_size: int, limit: int | None) -> int:
    from src.clients.mongodb_client import connect_mongodb
    from src.etl.load_mongodb import load_mongodb_records

    loaded = 0
    database = connect_mongodb()
    for batch in chunked(iter_records(input_path, limit=limit), batch_size):
        loaded += load_mongodb_records(database, batch)
    return loaded


def load_neo4j(input_path: str, batch_size: int, limit: int | None) -> int:
    from src.clients.neo4j_client import connect_neo4j
    from src.etl.load_neo4j import load_neo4j_records

    loaded = 0
    driver = connect_neo4j()
    try:
        for batch in chunked(iter_records(input_path, limit=limit), batch_size):
            loaded += load_neo4j_records(driver, batch)
    finally:
        driver.close()
    return loaded


def main() -> None:
    args = parse_args()
    input_path = str(Path(args.input))

    if args.dry_run:
        dry_run_summary(input_path, args.limit)
        return

    if args.backend == "mysql":
        print(f"Loaded {load_mysql(input_path, args.batch_size, args.limit)} records into MySQL.")
        return

    if args.backend == "mongodb":
        print(f"Loaded {load_mongodb(input_path, args.batch_size, args.limit)} records into MongoDB.")
        return

    if args.backend == "neo4j":
        print(f"Loaded {load_neo4j(input_path, args.batch_size, args.limit)} records into Neo4j.")
        return

    mysql_loaded = load_mysql(input_path, args.batch_size, args.limit)
    mongodb_loaded = load_mongodb(input_path, args.batch_size, args.limit)
    neo4j_loaded = load_neo4j(input_path, args.batch_size, args.limit)
    print(
        json.dumps(
            {
                "mysql_loaded": mysql_loaded,
                "mongodb_loaded": mongodb_loaded,
                "neo4j_loaded": neo4j_loaded,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
