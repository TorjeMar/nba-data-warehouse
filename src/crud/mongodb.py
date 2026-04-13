"""MongoDB warehouse loader."""

from __future__ import annotations

from typing import Iterable, Callable, Optional, TypeVar, Any

from pymongo import InsertOne, UpdateMany, DeleteMany
from pymongo.database import Database

from src.utils.wrapper import exception_handler
from dotenv import load_dotenv


load_dotenv()

T = TypeVar("T")

@exception_handler(silent=False)
def insert(
    database: Database, 
    records: Iterable[T], 
    collection_name: str,
    filter_fn: Optional[Callable[[T], bool]] = None,
    modifier: Optional[Callable[[T], T]] = None,
) -> int:
    
    filter_fn = filter_fn or (lambda x: True)
    modifier = modifier or (lambda x: x)
    
    records = map(modifier, filter(filter_fn, records))
    operations = list(map(InsertOne, records))

    if not operations:
        return 0

    result = database[collection_name].bulk_write(operations, ordered=False)
    return result.inserted_count

@exception_handler(silent=False)
def update(
    database: Database, 
    collection_name: str,
    records: Iterable[T], 
    identifier: Callable[[T], dict],
    filter_fn: Optional[Callable[[T], bool]] = None,
    modifier: Optional[Callable[[T], T]] = None,
    upsert: bool = True
) -> int:
    
    filter_fn = filter_fn or (lambda x: True)
    modifier = modifier or (lambda x: x)
    
    records = map(modifier, filter(filter_fn, records))

    operations = list(map(
        lambda record: UpdateMany(
            identifier(record),
            {"$set": record},
            upsert=upsert
        ),
        records
    ))

    if not operations:
        return 0

    result = database[collection_name].bulk_write(operations, ordered=False)
    return result.modified_count

@exception_handler(silent=False)
def delete(
    database: Database, 
    collection_name: str,
    records: Iterable[T],
    identifier: Callable[[T], dict],
    filter_fn: Optional[Callable[[T], bool]] = None,
) -> int:
    
    filter_fn = filter_fn or (lambda x: True)
    operations = list(map(
        lambda record: DeleteMany(identifier(record)), 
        filter(filter_fn, records)
    ))

    if not operations:
        return 0

    result = database[collection_name].bulk_write(operations, ordered=False)
    return result.deleted_count

@exception_handler(silent=False)
def query(
    database: Database, 
    collection_name: str,
    query_filter: dict[str, Any],
    projection: Optional[dict] = None,
) -> list[dict]:
    cursor = database[collection_name].find(query_filter, projection)
    return list(cursor)


if __name__ == "__main__":
    from src.clients import connect_mongodb
    from bson import ObjectId


    conn = connect_mongodb()

    if False:
        inserted_count = insert(
            database=conn,
            filter_fn=None,
            collection_name='raw_game_dates2',
            records=[
                {
                    "GAME_ID": "0030000001",
                    "GAME_DATE": "2001-02-11",
                    "TEAM_ID": 1610616833,
                    "TEAM_ABBREVIATION": "EST",
                    "MATCHUP": "EST vs. WST",
                    "SEASON_TYPE": "Regular Season",
                    "SEASON_LABEL": "2001-02",
                },
                {
                    "GAME_ID": "0030000001",
                    "GAME_DATE": "2001-02-11",
                    "TEAM_ID": 1610616834,
                    "TEAM_ABBREVIATION": "WST",
                    "MATCHUP": "WST @ EST",
                    "SEASON_TYPE": "Regular Season",
                    "SEASON_LABEL": "2001-02",
                }
            ]
        )

    if False:
        updated_count = update(
            database=conn,
            collection_name='raw_game_dates2',
            upsert=False,
            identifier=lambda record: {
                "GAME_ID": record["GAME_ID"],
                "TEAM_ABBREVIATION": "WST",
                "_id": ObjectId("69d62c5d0ebb9b5e52ab41ac")
            },
            records=[
                {
                    "GAME_ID": "0030000001",
                    "SEASON_TYPE": "2025",
                }
            ]
        )
    
    if False:
        deleted_count = delete(
            database=conn,
            collection_name='raw_game_dates2',
            identifier=lambda record: {
                "GAME_ID": record["GAME_ID"],
                "TEAM_ABBREVIATION": "WST",
                "_id": ObjectId("69d62c5d0ebb9b5e52ab41ac")
            },
            records=[
                {
                    "GAME_ID": "0030000001",
                    "SEASON_TYPE": "2025",
                }
            ]
        )
    
    if False:
        results = query(
            database=conn,
            collection_name='raw_game_dates2',
            query_filter={"GAME_ID": "0030000001"}
        )
        print(results)