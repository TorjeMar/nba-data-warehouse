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

MYSQL_UPSERT_DATE = """
INSERT INTO dim_date (
    date_key, full_date, day_of_month, month_num, month_name, quarter_num,
    year_num, day_of_week_num, day_of_week_name, is_weekend
) VALUES (
    %(date_key)s, %(full_date)s, %(day_of_month)s, %(month_num)s, %(month_name)s, %(quarter_num)s,
    %(year_num)s, %(day_of_week_num)s, %(day_of_week_name)s, %(is_weekend)s
)
ON DUPLICATE KEY UPDATE
    full_date = VALUES(full_date),
    day_of_month = VALUES(day_of_month),
    month_num = VALUES(month_num),
    month_name = VALUES(month_name),
    quarter_num = VALUES(quarter_num),
    year_num = VALUES(year_num),
    day_of_week_num = VALUES(day_of_week_num),
    day_of_week_name = VALUES(day_of_week_name),
    is_weekend = VALUES(is_weekend)
"""

MYSQL_UPSERT_GAME = """
INSERT INTO dim_game (
    source_game_id, season_label, game_date_key, matchup_label, home_team_key, away_team_key
) VALUES (
    %(source_game_id)s, %(season_label)s, %(game_date_key)s, %(matchup_label)s, %(home_team_key)s, %(away_team_key)s
)
ON DUPLICATE KEY UPDATE
    season_label = COALESCE(VALUES(season_label), season_label),
    game_date_key = COALESCE(VALUES(game_date_key), game_date_key),
    matchup_label = COALESCE(VALUES(matchup_label), matchup_label),
    home_team_key = COALESCE(VALUES(home_team_key), home_team_key),
    away_team_key = COALESCE(VALUES(away_team_key), away_team_key)
"""

MYSQL_UPDATE_GAME_HOME_AWAY_KEY = """
UPDATE dim_game g
JOIN dim_team t ON t.source_team_id = %(source_team_id)s
SET
    g.home_team_key = CASE
        WHEN %(home_away)s = 'home' THEN t.team_key
        ELSE g.home_team_key
    END,
    g.away_team_key = CASE
        WHEN %(home_away)s = 'away' THEN t.team_key
        ELSE g.away_team_key
    END
WHERE g.source_game_id = %(source_game_id)s
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
            date_params = None
            game_date_key = None
            if record.game_date is not None:
                game_date_key = int(record.game_date.strftime("%Y%m%d"))
                date_params = {
                    "date_key": game_date_key,
                    "full_date": record.game_date.date().isoformat(),
                    "day_of_month": record.game_date.day,
                    "month_num": record.game_date.month,
                    "month_name": record.game_date.strftime("%B"),
                    "quarter_num": ((record.game_date.month - 1) // 3) + 1,
                    "year_num": record.game_date.year,
                    "day_of_week_num": record.game_date.isoweekday(),
                    "day_of_week_name": record.game_date.strftime("%A"),
                    "is_weekend": record.game_date.isoweekday() >= 6,
                }

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
                "home_team_key": None,
                "away_team_key": None,
                "game_date_key": game_date_key,
            }
            game_key_params = {
                "source_game_id": record.source_game_id,
                "source_team_id": record.source_team_id,
                "home_away": record.home_away,
            }
            cursor.execute(MYSQL_UPSERT_TEAM, team_params)
            cursor.execute(MYSQL_UPSERT_PLAYER, player_params)
            if date_params is not None:
                cursor.execute(MYSQL_UPSERT_DATE, date_params)
            cursor.execute(MYSQL_UPSERT_GAME, game_params)
            cursor.execute(MYSQL_UPDATE_GAME_HOME_AWAY_KEY, game_key_params)
            cursor.execute(MYSQL_UPSERT_FACT, record.mysql_fact_params())
            loaded += 1
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
    return loaded
