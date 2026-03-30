"""Source extraction and transformation utilities."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Iterator

from src.etl.models import WarehouseRecord


def _normalize_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _to_int(value: Any) -> int:
    if value in (None, "", " "):
        return 0
    return int(float(value))


def _to_float(value: Any) -> float | None:
    if value in (None, "", " "):
        return None
    return float(value)


def _parse_minutes_to_seconds(value: Any) -> int:
    raw = _normalize_string(value)
    if not raw:
        return 0

    raw = raw.strip()

    import re

    # Normal case: MM:SS
    match = re.fullmatch(r"(\d+):(\d{1,2})", raw)
    if match:
        minutes, seconds = match.groups()
        return int(minutes) * 60 + int(seconds)

    # Repair malformed values like "0:0-57" -> "0:57"
    repaired = raw.replace("-", "")
    match = re.fullmatch(r"(\d+):(\d{1,2})", repaired)
    if match:
        minutes, seconds = match.groups()
        return int(minutes) * 60 + int(seconds)

    # Last-resort extraction of first plausible MM:SS pattern
    match = re.search(r"(\d+):(\d{1,2})", repaired)
    if match:
        minutes, seconds = match.groups()
        return int(minutes) * 60 + int(seconds)

    print(f"Warning: invalid minutes value {raw!r}, defaulting to 0")
    return 0


def _display_name(first_name: str | None, family_name: str | None, fallback: str | None) -> str:
    full_name = " ".join(part for part in [first_name, family_name] if part)
    if full_name:
        return full_name
    if fallback:
        return fallback
    return "Unknown Player"


def _sorted_row_keys(column_map: dict[str, Any]) -> list[str]:
    sample = next(iter(column_map.values()), {})
    if not isinstance(sample, dict):
        return []
    return sorted(sample.keys(), key=int)


def iter_source_rows(input_path: str | Path) -> Iterator[dict[str, Any]]:
    """Yield one flattened source row per player entry."""

    path = Path(input_path)
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            row_keys = _sorted_row_keys(payload)
            for row_key in row_keys:
                row = {column: values.get(row_key) for column, values in payload.items()}
                yield row


def build_record(row: dict[str, Any]) -> WarehouseRecord:
    first_name = _normalize_string(row.get("firstName")) or ""
    family_name = _normalize_string(row.get("familyName")) or ""
    display_name = _display_name(first_name, family_name, _normalize_string(row.get("nameI")))
    record = WarehouseRecord(
        source_game_id=str(row["gameId"]),
        source_team_id=_to_int(row.get("teamId")),
        team_city=_normalize_string(row.get("teamCity")) or "",
        team_name=_normalize_string(row.get("teamName")) or "",
        team_tricode=_normalize_string(row.get("teamTricode")) or "",
        team_slug=_normalize_string(row.get("teamSlug")) or "",
        source_person_id=_to_int(row.get("personId")),
        first_name=first_name,
        family_name=family_name,
        display_name=display_name,
        name_initial=_normalize_string(row.get("nameI")),
        player_slug=_normalize_string(row.get("playerSlug")),
        position_code=_normalize_string(row.get("position")),
        player_status_comment=_normalize_string(row.get("comment")),
        jersey_number=_normalize_string(row.get("jerseyNum")),
        minutes_raw=_normalize_string(row.get("minutes")),
        minutes_played_seconds=_parse_minutes_to_seconds(row.get("minutes")),
        field_goals_made=_to_int(row.get("fieldGoalsMade")),
        field_goals_attempted=_to_int(row.get("fieldGoalsAttempted")),
        field_goals_percentage=_to_float(row.get("fieldGoalsPercentage")),
        three_pointers_made=_to_int(row.get("threePointersMade")),
        three_pointers_attempted=_to_int(row.get("threePointersAttempted")),
        three_pointers_percentage=_to_float(row.get("threePointersPercentage")),
        free_throws_made=_to_int(row.get("freeThrowsMade")),
        free_throws_attempted=_to_int(row.get("freeThrowsAttempted")),
        free_throws_percentage=_to_float(row.get("freeThrowsPercentage")),
        rebounds_offensive=_to_int(row.get("reboundsOffensive")),
        rebounds_defensive=_to_int(row.get("reboundsDefensive")),
        rebounds_total=_to_int(row.get("reboundsTotal")),
        assists=_to_int(row.get("assists")),
        steals=_to_int(row.get("steals")),
        blocks=_to_int(row.get("blocks")),
        turnovers=_to_int(row.get("turnovers")),
        fouls_personal=_to_int(row.get("foulsPersonal")),
        points=_to_int(row.get("points")),
        plus_minus_points=float(row.get("plusMinusPoints") or 0.0),
    )
    record.source_row_hash = build_row_hash(record)
    return record


def iter_records(input_path: str | Path, limit: int | None = None) -> Iterator[WarehouseRecord]:
    yielded = 0
    for row in iter_source_rows(input_path):
        yield build_record(row)
        yielded += 1
        if limit is not None and yielded >= limit:
            return


def chunked(records: Iterable[WarehouseRecord], batch_size: int) -> Iterator[list[WarehouseRecord]]:
    batch: list[WarehouseRecord] = []
    for record in records:
        batch.append(record)
        if len(batch) >= batch_size:
            yield batch
            batch = []
    if batch:
        yield batch


def build_row_hash(record: WarehouseRecord) -> str:
    payload = {
        "source_game_id": record.source_game_id,
        "source_team_id": record.source_team_id,
        "source_person_id": record.source_person_id,
        "points": record.points,
        "assists": record.assists,
        "rebounds_total": record.rebounds_total,
        "minutes_played_seconds": record.minutes_played_seconds,
        "player_status_comment": record.player_status_comment,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def summarize_records(records: Iterable[WarehouseRecord]) -> dict[str, Any]:
    count = 0
    games: set[str] = set()
    teams: set[int] = set()
    players: set[int] = set()
    for record in records:
        count += 1
        games.add(record.source_game_id)
        teams.add(record.source_team_id)
        players.add(record.source_person_id)
    return {
        "rows": count,
        "games": len(games),
        "teams": len(teams),
        "players": len(players),
        "generated_at": datetime.utcnow().isoformat(timespec="seconds"),
    }
