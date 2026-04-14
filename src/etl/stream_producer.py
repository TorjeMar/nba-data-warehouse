"""Kafka producer for player-game warehouse events.

Reads the same source file as the original batch loader, reuses transform.py,
and publishes one Kafka event per player-game record.

Supports:
- --limit: maximum number of events to send
- --start-event: number of initial events to skip before producing
"""

from __future__ import annotations

import argparse
import json
from itertools import islice
from uuid import uuid4

from kafka import KafkaProducer
from tqdm import tqdm

from src.etl.stream_contract import build_player_game_event
from src.etl.transform import iter_records


DEFAULT_TOPIC = "player-game-records"
DEFAULT_BROKER = "localhost:29092"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Publish player-game records to Kafka.")
    parser.add_argument("--topic", default=DEFAULT_TOPIC, help="Kafka topic to publish to.")
    parser.add_argument("--broker", default=DEFAULT_BROKER, help="Kafka bootstrap server address.")
    parser.add_argument("--input", default="data/box_scores.jsonl", help="Path to the source box score JSONL file.")
    parser.add_argument("--producer-name", default="boxscore-producer", help="Producer name for trace metadata.")
    parser.add_argument("--producer-run-id", default=None, help="Run identifier for trace metadata.")
    parser.add_argument("--limit", type=int, default=None, help="Optional maximum number of events to send.")
    parser.add_argument(
        "--start-event",
        type=int,
        default=0,
        help="Number of initial player-game events to skip before producing.",
    )
    return parser.parse_args()


def build_producer(broker: str) -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=broker,
        acks="all",
        key_serializer=lambda value: value.encode("utf-8"),
        value_serializer=lambda value: json.dumps(value, default=str).encode("utf-8"),
    )


def iter_records_with_offset(input_path: str, start_event: int, limit: int | None):
    """
    Yield transformed records starting at the given zero-based event offset.

    Example:
    - start_event=0, limit=100 -> first 100 events
    - start_event=100000, limit=10000 -> events 100001..110000 (human counting)
    """
    base_iter = iter_records(input_path)
    sliced = islice(base_iter, start_event, None if limit is None else start_event + limit)
    return sliced


def run_producer(
    *,
    topic: str,
    broker: str,
    input_path: str,
    producer_name: str,
    producer_run_id: str,
    start_event: int = 0,
    limit: int | None = None,
) -> dict[str, int]:
    producer = build_producer(broker)
    sent = 0
    last_event_number = start_event

    progress = tqdm(
        total=limit,
        desc="Producing Kafka events",
        unit="events",
    )

    try:
        for absolute_event_number, record in enumerate(
            iter_records_with_offset(input_path, start_event=start_event, limit=limit),
            start=start_event + 1,
        ):
            event = build_player_game_event(
                record,
                source_file=input_path,
                source_line=absolute_event_number,
                producer_name=producer_name,
                producer_run_id=producer_run_id,
            )
            producer.send(topic, key=event["partition_key"], value=event).get(timeout=30)
            sent += 1
            last_event_number = absolute_event_number

            progress.update(1)
            progress.set_postfix(
                current_event=absolute_event_number,
                game=record.source_game_id,
                player=record.source_person_id,
            )
    finally:
        producer.flush()
        producer.close()
        progress.close()

    return {
        "sent": sent,
        "start_event": start_event,
        "last_event_number": last_event_number,
    }


def main() -> None:
    args = parse_args()
    if args.start_event < 0:
        raise ValueError("--start-event must be >= 0")
    if args.limit is not None and args.limit < 0:
        raise ValueError("--limit must be >= 0")

    producer_run_id = args.producer_run_id or str(uuid4())

    stats = run_producer(
        topic=args.topic,
        broker=args.broker,
        input_path=args.input,
        producer_name=args.producer_name,
        producer_run_id=producer_run_id,
        start_event=args.start_event,
        limit=args.limit,
    )

    output = {
        "topic": args.topic,
        "broker": args.broker,
        "producer_run_id": producer_run_id,
        **stats,
    }
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()