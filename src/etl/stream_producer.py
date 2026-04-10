"""Minimal Kafka producer for player-game warehouse events."""

from __future__ import annotations

import argparse
import json
from uuid import uuid4

from kafka import KafkaProducer

from src.etl.stream_contract import build_player_game_event
from src.etl.transform import iter_records


DEFAULT_TOPIC = "player-game-records"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Publish player-game records to Kafka.")
    parser.add_argument("--topic", default=DEFAULT_TOPIC, help="Kafka topic to publish to.")
    parser.add_argument("--broker", default="localhost:29092", help="Kafka bootstrap server address.")
    parser.add_argument("--input", default="data/box_scores.jsonl", help="Path to the source box score JSONL file.")
    parser.add_argument("--producer-name", default="boxscore-producer", help="Producer name for trace metadata.")
    parser.add_argument("--producer-run-id", default=None, help="Run identifier for trace metadata.")
    parser.add_argument("--limit", type=int, default=None, help="Optional record limit.")
    return parser.parse_args()


def build_producer(broker: str) -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=broker,
        key_serializer=lambda value: value.encode("utf-8"),
        value_serializer=lambda value: json.dumps(value, default=str).encode("utf-8"),
    )


def run_producer(
    *,
    topic: str,
    broker: str,
    input_path: str,
    producer_name: str,
    producer_run_id: str,
    limit: int | None = None,
) -> int:
    producer = build_producer(broker)
    sent = 0

    try:
        for source_line, record in enumerate(iter_records(input_path, limit=limit), start=1):
            event = build_player_game_event(
                record,
                source_file=input_path,
                source_line=source_line,
                producer_name=producer_name,
                producer_run_id=producer_run_id,
            )
            producer.send(topic, key=event["partition_key"], value=event).get(timeout=30)
            sent += 1
    finally:
        producer.flush()
        producer.close()

    return sent


def main() -> None:
    args = parse_args()
    producer_run_id = args.producer_run_id or str(uuid4())
    stats = {
        "topic": args.topic,
        "broker": args.broker,
        "producer_run_id": producer_run_id,
        "sent": run_producer(
            topic=args.topic,
            broker=args.broker,
            input_path=args.input,
            producer_name=args.producer_name,
            producer_run_id=producer_run_id,
            limit=args.limit,
        ),
    }
    print(json.dumps(stats, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
