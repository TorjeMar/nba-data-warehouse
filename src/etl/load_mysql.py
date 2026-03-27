"""MySQL warehouse loader."""

from __future__ import annotations

from typing import Iterable

from mysql.connector import MySQLConnection

from src.etl.models import WarehouseRecord


MYSQL_UPSERT_TEAM = """
INSERT INTO dim_team (
    source_team_id, team_tricode, team_name, team_city, team_slug
) VALUES (
    %(source_team_id)s, %(team_tricode)s, %(team_name)s, %(team_city)s, %(team_slug)s
)
ON DUPLICATE KEY UPDATE
    team_tricode = VALUES(team_tricode),
    team_name = VALUES(team_name),
    team_city = VALUES(team_city),
    team_slug = VALUES(team_slug)
"""

MYSQL_UPSERT_PLAYER = """
INSERT INTO dim_player (
    source_person_id, first_name, family_name, display_name, name_initial,
    player_slug, primary_position, jersey_number
) VALUES (
    %(source_person_id)s, %(first_name)s, %(family_name)s, %(display_name)s, %(name_initial)s,
    %(player_slug)s, %(position_code)s, %(jersey_number)s
)
ON DUPLICATE KEY UPDATE
    first_name = VALUES(first_name),
    family_name = VALUES(family_name),
    display_name = VALUES(display_name),
    name_initial = VALUES(name_initial),
    player_slug = VALUES(player_slug),
    primary_position = VALUES(primary_position),
    jersey_number = VALUES(jersey_number)
"""

MYSQL_UPSERT_GAME = """
INSERT INTO dim_game (
    source_game_id, season_label, matchup_label
) VALUES (
    %(source_game_id)s, %(season_label)s, %(matchup_label)s
)
ON DUPLICATE KEY UPDATE
    season_label = COALESCE(VALUES(season_label), season_label),
    matchup_label = COALESCE(VALUES(matchup_label), matchup_label)
"""

MYSQL_UPSERT_FACT = """
INSERT INTO fact_player_game_stats (
    game_key,
    team_key,
    player_key,
    position_key,
    minutes_played_seconds,
    field_goals_made,
    field_goals_attempted,
    field_goals_percentage,
    three_pointers_made,
    three_pointers_attempted,
    three_pointers_percentage,
    free_throws_made,
    free_throws_attempted,
    free_throws_percentage,
    rebounds_offensive,
    rebounds_defensive,
    rebounds_total,
    assists,
    steals,
    blocks,
    turnovers,
    fouls_personal,
    points,
    plus_minus_points,
    player_status_comment,
    source_row_hash
)
SELECT
    g.game_key,
    t.team_key,
    p.player_key,
    pos.position_key,
    %(minutes_played_seconds)s,
    %(field_goals_made)s,
    %(field_goals_attempted)s,
    %(field_goals_percentage)s,
    %(three_pointers_made)s,
    %(three_pointers_attempted)s,
    %(three_pointers_percentage)s,
    %(free_throws_made)s,
    %(free_throws_attempted)s,
    %(free_throws_percentage)s,
    %(rebounds_offensive)s,
    %(rebounds_defensive)s,
    %(rebounds_total)s,
    %(assists)s,
    %(steals)s,
    %(blocks)s,
    %(turnovers)s,
    %(fouls_personal)s,
    %(points)s,
    %(plus_minus_points)s,
    %(player_status_comment)s,
    %(source_row_hash)s
FROM dim_game g
JOIN dim_team t ON t.source_team_id = %(source_team_id)s
JOIN dim_player p ON p.source_person_id = %(source_person_id)s
LEFT JOIN dim_position pos ON pos.position_code = %(position_code)s
WHERE g.source_game_id = %(source_game_id)s
ON DUPLICATE KEY UPDATE
    position_key = VALUES(position_key),
    minutes_played_seconds = VALUES(minutes_played_seconds),
    field_goals_made = VALUES(field_goals_made),
    field_goals_attempted = VALUES(field_goals_attempted),
    field_goals_percentage = VALUES(field_goals_percentage),
    three_pointers_made = VALUES(three_pointers_made),
    three_pointers_attempted = VALUES(three_pointers_attempted),
    three_pointers_percentage = VALUES(three_pointers_percentage),
    free_throws_made = VALUES(free_throws_made),
    free_throws_attempted = VALUES(free_throws_attempted),
    free_throws_percentage = VALUES(free_throws_percentage),
    rebounds_offensive = VALUES(rebounds_offensive),
    rebounds_defensive = VALUES(rebounds_defensive),
    rebounds_total = VALUES(rebounds_total),
    assists = VALUES(assists),
    steals = VALUES(steals),
    blocks = VALUES(blocks),
    turnovers = VALUES(turnovers),
    fouls_personal = VALUES(fouls_personal),
    points = VALUES(points),
    plus_minus_points = VALUES(plus_minus_points),
    player_status_comment = VALUES(player_status_comment),
    source_row_hash = VALUES(source_row_hash),
    updated_at = CURRENT_TIMESTAMP
"""


def load_mysql_records(connection: MySQLConnection, records: Iterable[WarehouseRecord]) -> int:
    cursor = connection.cursor()
    loaded = 0
    try:
        for record in records:
            team_params = {
                "source_team_id": record.source_team_id,
                "team_tricode": record.team_tricode,
                "team_name": record.team_name,
                "team_city": record.team_city,
                "team_slug": record.team_slug,
            }
            player_params = {
                "source_person_id": record.source_person_id,
                "first_name": record.first_name,
                "family_name": record.family_name,
                "display_name": record.display_name,
                "name_initial": record.name_initial,
                "player_slug": record.player_slug,
                "position_code": record.position_code or "",
                "jersey_number": record.jersey_number,
            }
            game_params = {
                "source_game_id": record.source_game_id,
                "season_label": record.season_label,
                "matchup_label": record.matchup_label,
            }
            cursor.execute(MYSQL_UPSERT_TEAM, team_params)
            cursor.execute(MYSQL_UPSERT_PLAYER, player_params)
            cursor.execute(MYSQL_UPSERT_GAME, game_params)
            cursor.execute(MYSQL_UPSERT_FACT, record.mysql_fact_params())
            loaded += 1
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
    return loaded
