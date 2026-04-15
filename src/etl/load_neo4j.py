"""Neo4j warehouse loader.

Uses separate MERGE queries per entity type with pre-deduplication
for performance — avoids redundant lock contention on shared nodes.
"""

from __future__ import annotations

from typing import Iterable

from neo4j import Driver, ManagedTransaction

from src.etl.models import WarehouseRecord


# -- Queries ------------------------------------------------------------------

MERGE_TEAMS = """
UNWIND $rows AS row
MERGE (t:Team {sourceTeamId: row.sourceTeamId})
SET t.teamName = row.teamName, t.teamCity = row.teamCity,
    t.teamTricode = row.teamTricode, t.teamSlug = row.teamSlug
"""

MERGE_PLAYERS = """
UNWIND $rows AS row
MERGE (p:Player {sourcePersonId: row.sourcePersonId})
SET p.firstName = row.firstName, p.familyName = row.familyName,
    p.displayName = row.displayName, p.nameInitial = row.nameInitial,
    p.playerSlug = row.playerSlug, p.jerseyNumber = row.jerseyNumber
"""

MERGE_POSITIONS = """
UNWIND $rows AS row
MERGE (:Position {positionCode: row.positionCode})
"""

MERGE_GAMES = """
UNWIND $rows AS row
MERGE (g:Game {sourceGameId: row.sourceGameId})
SET g.gameType = row.gameType, g.seasonLabel = row.seasonLabel, g.matchupLabel = row.matchupLabel
"""

MERGE_DATES = """
UNWIND $rows AS row
MERGE (d:Date {dateKey: row.dateKey})
SET d.fullDate = date(row.gameDate),
    d.yearNum = row.yearNum, d.monthNum = row.monthNum,
    d.monthName = row.monthName, d.quarterNum = row.quarterNum,
    d.dayOfMonth = row.dayOfMonth, d.dayOfWeekNum = row.dayOfWeekNum,
    d.dayOfWeekName = row.dayOfWeekName, d.isWeekend = row.isWeekend
"""

MERGE_PLAYER_POSITION = """
UNWIND $rows AS row
MATCH (p:Player {sourcePersonId: row.sourcePersonId})
MATCH (pos:Position {positionCode: row.positionCode})
MERGE (p)-[:HAS_POSITION]->(pos)
"""

MERGE_PLAYER_TEAM = """
UNWIND $rows AS row
MATCH (p:Player {sourcePersonId: row.sourcePersonId})
MATCH (t:Team {sourceTeamId: row.sourceTeamId})
MERGE (p)-[:REPRESENTED_TEAM]->(t)
"""

MERGE_GAME_DATE = """
UNWIND $rows AS row
MATCH (g:Game {sourceGameId: row.sourceGameId})
MATCH (d:Date {dateKey: row.dateKey})
MERGE (g)-[:ON_DATE]->(d)
"""

MERGE_PLAYED_IN = """
UNWIND $rows AS row
MATCH (p:Player {sourcePersonId: row.sourcePersonId})
MATCH (g:Game {sourceGameId: row.sourceGameId})
MERGE (p)-[r:PLAYED_IN {sourceGameId: row.sourceGameId, sourceTeamId: row.sourceTeamId}]->(g)
SET r.homeAway = row.homeAway,
    r.secondsPlayed = row.minutesPlayedSeconds,
    r.fieldGoalsMade = row.fieldGoalsMade,
    r.fieldGoalsAttempted = row.fieldGoalsAttempted,
    r.fieldGoalsPercentage = row.fieldGoalsPercentage,
    r.threePointersMade = row.threePointersMade,
    r.threePointersAttempted = row.threePointersAttempted,
    r.threePointersPercentage = row.threePointersPercentage,
    r.freeThrowsMade = row.freeThrowsMade,
    r.freeThrowsAttempted = row.freeThrowsAttempted,
    r.freeThrowsPercentage = row.freeThrowsPercentage,
    r.reboundsOffensive = row.reboundsOffensive,
    r.reboundsDefensive = row.reboundsDefensive,
    r.reboundsTotal = row.reboundsTotal,
    r.assists = row.assists, r.steals = row.steals,
    r.blocks = row.blocks, r.turnovers = row.turnovers,
    r.foulsPersonal = row.foulsPersonal, r.points = row.points,
    r.plusMinusPoints = row.plusMinusPoints,
    r.playerStatusComment = row.playerStatusComment,
    r.updatedAt = datetime()
"""


# -- Helpers ------------------------------------------------------------------

def _dedup(rows: list[dict], *keys: str) -> list[dict]:
    """Keep last occurrence per composite key."""
    seen: dict[tuple, dict] = {}
    for row in rows:
        seen[tuple(row[k] for k in keys)] = row
    return list(seen.values())


def _pick(rows: list[dict], *fields: str) -> list[dict]:
    """Project rows down to the given fields."""
    return [{f: row[f] for f in fields} for row in rows]


def _run(tx: ManagedTransaction, query: str, rows: list[dict]) -> None:
    if rows:
        tx.run(query, rows=rows).consume()


# -- Public API ---------------------------------------------------------------

def load_neo4j_records(driver: Driver, records: Iterable[WarehouseRecord]) -> int:
    rows = [r.neo4j_params() for r in records]
    if not rows:
        return 0

    teams = _dedup(_pick(rows, "sourceTeamId", "teamName", "teamCity", "teamTricode", "teamSlug"), "sourceTeamId")
    players = _dedup(_pick(rows, "sourcePersonId", "firstName", "familyName", "displayName", "nameInitial", "playerSlug", "jerseyNumber"), "sourcePersonId")
    positions = _dedup([{"positionCode": r["positionCode"] or ""} for r in rows], "positionCode")
    games = _dedup(_pick(rows, "sourceGameId", "seasonLabel", "matchupLabel"), "sourceGameId")
    dates = _dedup(
        [_pick([r], "dateKey", "gameDate", "yearNum", "monthNum", "monthName", "quarterNum", "dayOfMonth", "dayOfWeekNum", "dayOfWeekName", "isWeekend")[0]
         for r in rows if r["dateKey"] and r["gameDate"]],
        "dateKey",
    )
    player_positions = _dedup([{"sourcePersonId": r["sourcePersonId"], "positionCode": r["positionCode"] or ""} for r in rows], "sourcePersonId", "positionCode")
    player_teams = _dedup(_pick(rows, "sourcePersonId", "sourceTeamId"), "sourcePersonId", "sourceTeamId")
    game_dates = _dedup(
        [_pick([r], "sourceGameId", "dateKey")[0] for r in rows if r["dateKey"]],
        "sourceGameId", "dateKey",
    )

    def write_batch(tx: ManagedTransaction) -> None:
        _run(tx, MERGE_TEAMS, teams)
        _run(tx, MERGE_PLAYERS, players)
        _run(tx, MERGE_POSITIONS, positions)
        _run(tx, MERGE_GAMES, games)
        _run(tx, MERGE_DATES, dates)
        _run(tx, MERGE_PLAYER_POSITION, player_positions)
        _run(tx, MERGE_PLAYER_TEAM, player_teams)
        _run(tx, MERGE_GAME_DATE, game_dates)
        _run(tx, MERGE_PLAYED_IN, rows)

    with driver.session() as session:
        session.execute_write(write_batch)
    return len(rows)
