"""Minimal streaming contract for player-game warehouse records."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from src.etl.models import WarehouseRecord


EVENT_TYPE = "player_game_record"
SCHEMA_VERSION = "1.0.0"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _to_iso_utc(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _parse_iso_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def build_player_game_event(
    record: WarehouseRecord,
    *,
    source_file: str,
    source_line: int,
    producer_name: str,
    producer_run_id: str,
) -> dict[str, Any]:
    payload = asdict(record)
    payload["game_date"] = _to_iso_utc(record.game_date)
    return {
        "event_id": str(uuid4()),
        "event_type": EVENT_TYPE,
        "schema_version": SCHEMA_VERSION,
        "partition_key": f"{record.source_game_id}:{record.source_team_id}",
        "ingested_at_utc": _utc_now_iso(),
        "trace": {
            "producer_name": producer_name,
            "producer_run_id": producer_run_id,
            "source_file": source_file,
            "source_line": source_line,
        },
        "payload": payload,
    }


def assert_valid_player_game_event(event: dict[str, Any]) -> None:
    if event.get("event_type") != EVENT_TYPE:
        raise ValueError(f"event_type must be '{EVENT_TYPE}'")
    if event.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"schema_version must be '{SCHEMA_VERSION}'")
    if not isinstance(event.get("payload"), dict):
        raise ValueError("payload must be an object")


def event_to_warehouse_record(event: dict[str, Any]) -> WarehouseRecord:
    assert_valid_player_game_event(event)
    payload = dict(event["payload"])
    payload["game_date"] = _parse_iso_datetime(payload.get("game_date"))
    return WarehouseRecord(**payload)
