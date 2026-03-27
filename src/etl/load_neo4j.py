"""Neo4j warehouse loader."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from neo4j import Driver

from src.etl.models import WarehouseRecord


PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOAD_QUERY = (PROJECT_ROOT / "sql" / "neo4j" / "004_load_shape.cypher").read_text(encoding="utf-8")


def load_neo4j_records(driver: Driver, records: Iterable[WarehouseRecord]) -> int:
    loaded = 0
    with driver.session() as session:
        for record in records:
            session.execute_write(lambda tx, params: tx.run(LOAD_QUERY, params), record.neo4j_params())
            loaded += 1
    return loaded
