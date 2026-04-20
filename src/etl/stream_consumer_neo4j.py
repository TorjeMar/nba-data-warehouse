"""Kafka consumer that batches player-game events and loads them into Neo4j."""

from __future__ import annotations

import argparse
import json
import sys
import time
from typing import Callable

from kafka import KafkaConsumer
from tqdm import tqdm

from src.clients.neo4j_client import connect_neo4j
from src.etl.load_neo4j import load_neo4j_records
from src.etl.stream_contract import event_to_warehouse_record


DEFAULT_TOPIC = "player-game-records"
DEFAULT_BROKER = "localhost:29092"
DEFAULT_GROUP_ID = "neo4j-loader"
DEFAULT_BATCH_SIZE = 5000
DEFAULT_FLUSH_INTERVAL_SECONDS = 5.0
DEFAULT_POLL_TIMEOUT_MS = 1000


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Consume player-game records from Kafka into Neo4j.")
    parser.add_argument("--topic", default=DEFAULT_TOPIC)
    parser.add_argument("--broker", default=DEFAULT_BROKER)
    parser.add_argument("--group-id", default=DEFAULT_GROUP_ID)
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--flush-interval-seconds", type=float, default=DEFAULT_FLUSH_INTERVAL_SECONDS)
    parser.add_argument("--limit", type=int, default=None, help="Optional maximum number of messages to consume.")
    parser.add_argument("--poll-timeout-ms", type=int, default=DEFAULT_POLL_TIMEOUT_MS)
    parser.add_argument(
        "--idle-polls-before-exit",
        type=int,
        default=None,
        help="Exit after this many consecutive empty polls.",
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
        consumer_timeout_ms=1000,
    )


def flush_batch(driver, batch: list, commit_fn: Callable[[], None], stats: dict[str, int]) -> int:
    if not batch:
        return 0

    loaded = load_neo4j_records(driver, batch)
    commit_fn()

    stats["loaded"] += loaded
    stats["flushes"] += 1

    flushed_count = len(batch)
    batch.clear()
    return flushed_count


def run_consumer(
    *,
    topic: str,
    broker: str,
    group_id: str,
    batch_size: int,
    flush_interval_seconds: float,
    poll_timeout_ms: int = DEFAULT_POLL_TIMEOUT_MS,
    idle_polls_before_exit: int | None = None,
    limit: int | None = None,
) -> dict[str, int]:
    consumer = build_consumer(topic, broker, group_id)
    driver = connect_neo4j()

    batch = []
    stats = {
        "consumed": 0,
        "loaded": 0,
        "invalid": 0,
        "failed": 0,
        "flushes": 0,
    }
    last_flush = time.monotonic()
    idle_polls = 0

    progress = tqdm(
        total=limit,
        desc="Neo4j",
        unit="ev",
        file=sys.stdout,
        dynamic_ncols=False,
        ncols=100,
        mininterval=0.2,
        maxinterval=0.5,
        smoothing=0.1,
        leave=True,
    )

    try:
        while limit is None or stats["consumed"] < limit:
            records = consumer.poll(timeout_ms=poll_timeout_ms, max_records=max(1, batch_size))
            received_any = False

            for _, messages in records.items():
                received_any = True
                for message in messages:
                    if limit is not None and stats["consumed"] >= limit:
                        break

                    stats["consumed"] += 1
                    progress.update(1)

                    try:
                        batch.append(event_to_warehouse_record(message.value))
                    except Exception:
                        stats["invalid"] += 1

                    progress.set_postfix_str(
                        f"loaded={stats['loaded']} batch={len(batch)} flushes={stats['flushes']} invalid={stats['invalid']}",
                        refresh=False,
                    )

            if received_any:
                idle_polls = 0
            else:
                idle_polls += 1

            now = time.monotonic()
            should_flush = len(batch) >= batch_size or (batch and now - last_flush >= flush_interval_seconds)

            if should_flush:
                try:
                    flush_batch(driver, batch, consumer.commit, stats)
                    last_flush = now

                    progress.set_postfix_str(
                        f"loaded={stats['loaded']} batch={len(batch)} flushes={stats['flushes']} invalid={stats['invalid']}",
                        refresh=False,
                    )
                except Exception:
                    stats["failed"] += len(batch)
                    raise

            if not received_any and batch and now - last_flush >= flush_interval_seconds:
                flush_batch(driver, batch, consumer.commit, stats)
                last_flush = now

                progress.set_postfix_str(
                    f"loaded={stats['loaded']} batch={len(batch)} flushes={stats['flushes']} invalid={stats['invalid']}",
                    refresh=False,
                )

            if not received_any and not batch and idle_polls_before_exit is not None and idle_polls >= idle_polls_before_exit:
                break

        if batch:
            flush_batch(driver, batch, consumer.commit, stats)

            progress.set_postfix_str(
                f"loaded={stats['loaded']} batch={len(batch)} flushes={stats['flushes']} invalid={stats['invalid']}",
                refresh=False,
            )

    finally:
        progress.close()
        consumer.close()
        driver.close()

    return stats


def main() -> None:
    args = parse_args()
    stats = run_consumer(
        topic=args.topic,
        broker=args.broker,
        group_id=args.group_id,
        batch_size=args.batch_size,
        flush_interval_seconds=args.flush_interval_seconds,
        poll_timeout_ms=args.poll_timeout_ms,
        idle_polls_before_exit=args.idle_polls_before_exit,
        limit=args.limit,
    )
    print(json.dumps(stats, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
