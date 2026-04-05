"""Neo4j connection helpers."""

from __future__ import annotations

import os

from neo4j import GraphDatabase
from neo4j import Driver
from dotenv import load_dotenv


load_dotenv()


def connect_neo4j() -> Driver:
    uri = os.getenv("NEO4J_URI", "bolt://127.0.0.1:7687")
    username = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD") or os.getenv("DB_PASSWORD")
    return GraphDatabase.driver(uri, auth=(username, password))
