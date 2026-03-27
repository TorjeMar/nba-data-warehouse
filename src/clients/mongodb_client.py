"""MongoDB connection helpers."""

from __future__ import annotations

import os

from pymongo import MongoClient
from pymongo.database import Database


def connect_mongodb() -> Database:
    username = os.getenv("DB_USERNAME")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("MONGODB_HOST", "127.0.0.1")
    port = int(os.getenv("MONGODB_PORT", "27017"))
    database_name = os.getenv("MONGODB_DATABASE", "mydatabase")

    if username and password:
        uri = (
            f"mongodb://{username}:{password}@{host}:{port}/{database_name}"
            "?authSource=admin"
        )
    else:
        uri = f"mongodb://{host}:{port}/{database_name}"
    client = MongoClient(uri)
    return client[database_name]
