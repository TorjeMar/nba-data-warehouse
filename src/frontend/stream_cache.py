from __future__ import annotations

import json
import threading
import time
from typing import Any

from kafka import KafkaConsumer


DEFAULT_BROKER = "localhost:29092"
TEAM_TOPIC = "TEAM_STREAM_TOTALS"
PLAYER_TOPIC = "PLAYER_STREAM_TOTALS"


class StreamStateCache:
    def __init__(self, broker: str = DEFAULT_BROKER) -> None:
        self.broker = broker
        self._lock = threading.RLock()

        self.team_rows: dict[int, dict[str, Any]] = {}
        self.player_rows: dict[int, dict[str, Any]] = {}

        self.started = False
        self.ready = False
        self.last_update_ts: float | None = None

    def start(self) -> None:
        if self.started:
            return
        self.started = True
        thread = threading.Thread(target=self._run, name="stream-state-cache", daemon=True)
        thread.start()

    def _build_consumer(self) -> KafkaConsumer:
        return KafkaConsumer(
            TEAM_TOPIC,
            PLAYER_TOPIC,
            bootstrap_servers=self.broker,
            group_id="stream-dashboard-cache",
            enable_auto_commit=True,
            auto_offset_reset="earliest",
            consumer_timeout_ms=1000,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")) if v else None,
            key_deserializer=lambda v: v.decode("utf-8") if v else None,
        )

    def _run(self) -> None:
        while True:
            consumer = None
            try:
                consumer = self._build_consumer()

                while True:
                    records = consumer.poll(timeout_ms=1000, max_records=500)

                    if not self.ready:
                        self.ready = True

                    for topic_partition, messages in records.items():
                        topic = topic_partition.topic

                        for message in messages:
                            if message.value is None:
                                continue

                            if topic == TEAM_TOPIC:
                                self._apply_team_update(message.value)
                            elif topic == PLAYER_TOPIC:
                                self._apply_player_update(message.value)

                            self.last_update_ts = time.time()

            except Exception as exc:
                print(f"[stream-cache] consumer error: {exc}")
                time.sleep(2)
            finally:
                if consumer is not None:
                    try:
                        consumer.close()
                    except Exception:
                        pass

    def _normalize_team_row(self, row: dict[str, Any]) -> dict[str, Any]:
        # ksql table output may come in either flat or nested shape depending on serialization
        if "SOURCE_TEAM_ID" in row:
            return row
        if "ROW" in row and isinstance(row["ROW"], dict):
            return row["ROW"]
        return row

    def _normalize_player_row(self, row: dict[str, Any]) -> dict[str, Any]:
        if "SOURCE_PERSON_ID" in row:
            return row
        if "ROW" in row and isinstance(row["ROW"], dict):
            return row["ROW"]
        return row

    def _apply_team_update(self, raw_row: dict[str, Any]) -> None:
        row = self._normalize_team_row(raw_row)

        team_id = row.get("SOURCE_TEAM_ID")
        if team_id in (None, ""):
            return

        try:
            team_id = int(team_id)
        except (TypeError, ValueError):
            return

        with self._lock:
            self.team_rows[team_id] = {
                "team_id": team_id,
                "team_tricode": row.get("TEAM_TRICODE"),
                "team_city": row.get("TEAM_CITY"),
                "team_name_raw": row.get("TEAM_NAME"),
                "games_seen": int(row.get("GAMES_SEEN", 0) or 0),
                "total_points": int(row.get("TOTAL_POINTS", 0) or 0),
                "total_assists": int(row.get("TOTAL_ASSISTS", 0) or 0),
                "total_rebounds": int(row.get("TOTAL_REBOUNDS", 0) or 0),
                "total_turnovers": int(row.get("TOTAL_TURNOVERS", 0) or 0),
            }

    def _apply_player_update(self, raw_row: dict[str, Any]) -> None:
        row = self._normalize_player_row(raw_row)

        player_id = row.get("SOURCE_PERSON_ID")
        if player_id in (None, ""):
            return

        try:
            player_id = int(player_id)
        except (TypeError, ValueError):
            return

        with self._lock:
            self.player_rows[player_id] = {
                "source_person_id": player_id,
                "display_name": row.get("DISPLAY_NAME"),
                "team_tricode": row.get("TEAM_TRICODE"),
                "total_points": int(row.get("TOTAL_POINTS", 0) or 0),
                "total_assists": int(row.get("TOTAL_ASSISTS", 0) or 0),
                "total_rebounds": int(row.get("TOTAL_REBOUNDS", 0) or 0),
                "player_rows_seen": int(row.get("PLAYER_ROWS_SEEN", 0) or 0),
            }

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "ready": self.ready,
                "last_update_ts": self.last_update_ts,
                "teams": list(self.team_rows.values()),
                "players": list(self.player_rows.values()),
            }