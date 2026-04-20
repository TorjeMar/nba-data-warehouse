"""MongoDB warehouse loader."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

from pymongo import UpdateOne
from pymongo.database import Database

from src.etl.models import WarehouseRecord
from dotenv import load_dotenv

load_dotenv()

def load_mongodb_records(database: Database, records: Iterable[WarehouseRecord]) -> int:
    """Upsert warehouse rows by natural key."""
    deduped_records: dict[tuple[str, int, int], WarehouseRecord] = {}

    for record in records:
        key = (record.source_game_id, record.source_team_id, record.source_person_id)
        # Keep the latest occurrence in the batch so restreamed rows refresh the document.
        deduped_records[key] = record

    return update_mongodb_records(database, deduped_records.values())


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
