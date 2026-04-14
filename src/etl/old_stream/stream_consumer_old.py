"""Minimal Kafka consumer for player-game warehouse events."""

from __future__ import annotations

import argparse
import json
from typing import Any, Callable

from kafka import KafkaConsumer

from src.clients.mongodb_client import connect_mongodb
from src.clients.mysql_client import connect_mysql
from src.clients.neo4j_client import connect_neo4j
from src.etl.load_mongodb import load_mongodb_records
from src.etl.load_mysql import load_mysql_records
from src.etl.load_neo4j import load_neo4j_records
from src.etl.stream_contract import event_to_warehouse_record


DEFAULT_TOPIC = "player-game-records"
DEFAULT_GROUP_ID = "player-game-consumer"
DEFAULT_BACKEND = "mysql"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Consume player-game records from Kafka.")
    parser.add_argument("--topic", default=DEFAULT_TOPIC, help="Kafka topic to consume from.")
    parser.add_argument("--broker", default="localhost:29092", help="Kafka bootstrap server address.")
    parser.add_argument("--group-id", default=DEFAULT_GROUP_ID, help="Kafka consumer group id.")
    parser.add_argument(
        "--backend",
        choices=["mysql", "mongodb", "neo4j"],
        default=DEFAULT_BACKEND,
        help="Warehouse backend to load into.",
    )
    parser.add_argument("--limit", type=int, default=None, help="Optional maximum number of messages to process.")
    parser.add_argument(
        "--poll-timeout-ms",
        type=int,
        default=1000,
        help="Kafka poll timeout in milliseconds.",
    )
    parser.add_argument(
        "--idle-polls-before-exit",
        type=int,
        default=None,
        help="Exit after this many consecutive empty polls. Useful for scheduled one-shot runs.",
    )
    return parser.parse_args()


def build_consumer(topic: str, broker: str, group_id: str) -> KafkaConsumer:
    return KafkaConsumer(
        topic,
        bootstrap_servers=broker,
        group_id=group_id,
        enable_auto_commit=False,
        auto_offset_reset="earliest",
        value_deserializer=lambda value: json.loads(value.decode("utf-8")),
        key_deserializer=lambda value: value.decode("utf-8") if value is not None else None,
    )


def build_backend(backend: str) -> tuple[Any, Callable[[Any, list[Any]], int], Callable[[Any], None]]:
    if backend == "mysql":
        return connect_mysql(), load_mysql_records, lambda resource: resource.close()
    if backend == "mongodb":
        return connect_mongodb(), load_mongodb_records, lambda resource: resource.client.close()
    if backend == "neo4j":
        return connect_neo4j(), load_neo4j_records, lambda resource: resource.close()
    raise ValueError(f"Unsupported backend: {backend}")


def run_consumer(
    *,
    topic: str,
    broker: str,
    group_id: str,
    backend: str,
    limit: int | None = None,
    poll_timeout_ms: int = 1000,
    idle_polls_before_exit: int | None = None,
) -> dict[str, int]:
    consumer = build_consumer(topic, broker, group_id)
    resource, loader, close_resource = build_backend(backend)
    stats = {"consumed": 0, "loaded": 0, "invalid": 0, "failed": 0}
    consecutive_idle_polls = 0

    try:
        while limit is None or stats["consumed"] < limit:
            records = consumer.poll(timeout_ms=poll_timeout_ms, max_records=1)
            if not records:
                consecutive_idle_polls += 1
                if (
                    idle_polls_before_exit is not None
                    and consecutive_idle_polls >= idle_polls_before_exit
                ):
                    break
                continue
            consecutive_idle_polls = 0

            for _, messages in records.items():
                for message in messages:
                    if limit is not None and stats["consumed"] >= limit:
                        break

                    stats["consumed"] += 1

                    try:
                        record = event_to_warehouse_record(message.value)
                    except Exception:
                        stats["invalid"] += 1
                        consumer.commit()
                        continue

                    try:
                        stats["loaded"] += loader(resource, [record])
                    except Exception:
                        stats["failed"] += 1
                        consumer.commit()
                        continue

                    consumer.commit()
    finally:
        consumer.close()
        close_resource(resource)

    return stats


def main() -> None:
    args = parse_args()
    stats = run_consumer(
        topic=args.topic,
        broker=args.broker,
        group_id=args.group_id,
        backend=args.backend,
        limit=args.limit,
        poll_timeout_ms=args.poll_timeout_ms,
        idle_polls_before_exit=args.idle_polls_before_exit,
    )
    print(json.dumps(stats, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
