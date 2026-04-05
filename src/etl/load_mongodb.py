"""MongoDB warehouse loader."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

from pymongo import InsertOne, UpdateOne
from pymongo.database import Database
from pymongo.errors import BulkWriteError

from src.etl.models import WarehouseRecord
from dotenv import load_dotenv

load_dotenv()

def load_mongodb_records(database: Database, records: Iterable[WarehouseRecord]) -> int:
    """Insert-only load. Existing rows and duplicate keys are ignored."""
    operations = []
    seen_keys: set[tuple[str, int, int]] = set()

    for record in records:
        key = (record.source_game_id, record.source_team_id, record.source_person_id)
        if key in seen_keys:
            # Keep the first row and ignore later duplicates in this batch.
            continue
        seen_keys.add(key)

        document = record.mongodb_document()
        operations.append(InsertOne(document))

    if not operations:
        return 0

    try:
        result = database.player_game_stats.bulk_write(operations, ordered=False)
        return result.inserted_count
    except BulkWriteError as exc:
        details = exc.details or {}
        write_errors = details.get("writeErrors", [])
        non_duplicate_errors = [err for err in write_errors if err.get("code") != 11000]
        if non_duplicate_errors:
            raise
        return int(details.get("nInserted", 0))


def update_mongodb_records(database: Database, records: Iterable[WarehouseRecord]) -> int:
    """Update existing rows by key, inserting if missing."""
    operations = []
    for record in records:
        document = record.mongodb_document()
        created_at = document.pop("createdAt", datetime.now(timezone.utc))
        document["updatedAt"] = datetime.now(timezone.utc)
        operations.append(
            UpdateOne(
                {
                    "sourceGameId": record.source_game_id,
                    "team.sourceTeamId": record.source_team_id,
                    "player.sourcePersonId": record.source_person_id,
                },
                {
                    "$set": document,
                    "$setOnInsert": {"createdAt": created_at},
                },
                upsert=True,
            )
        )

    if not operations:
        return 0

    _ = database.player_game_stats.bulk_write(operations, ordered=False)
    return len(operations)