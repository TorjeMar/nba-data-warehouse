"""MongoDB warehouse loader."""

from __future__ import annotations

import os

from typing import Iterable

from pymongo import UpdateOne, InsertOne
from pymongo.database import Database

from src.etl.models import WarehouseRecord
from dotenv import load_dotenv

load_dotenv()

def load_mongodb_records(database: Database, records: Iterable[WarehouseRecord]) -> int:
    operations = []
    for record in records:
        document = record.mongodb_document()
        operations.append(
            UpdateOne(
                {
                    "sourceGameId": record.source_game_id,
                    "team.sourceTeamId": record.source_team_id,
                    "player.sourcePersonId": record.source_person_id,
                },
                {"$set": document},
                upsert=True,
            )
        )

    if not operations:
        return 0

    result = database.player_game_stats.bulk_write(operations, ordered=False)
    return result.upserted_count + result.modified_count


def load_mongodb_records(database: Database, records: Iterable[WarehouseRecord]) -> int:
    operations = []
    for record in records:
        document = record.mongodb_document()
        operations.append(
            InsertOne(
                document,
                namespace=os.environ["DB_NAME"],
            )
        )

    if not operations:
        return 0

    result = database.player_game_stats.bulk_write(operations, ordered=False)
    return result.upserted_count + result.modified_count
