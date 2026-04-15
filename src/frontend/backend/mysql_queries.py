"""MySQL query functions for the frontend."""

from __future__ import annotations

from src.clients.mysql_client import connect_mysql
from src.frontend.backend.constants import PLAYOFF_ROUND_NAMES
from src.frontend.backend.season_payloads import (
    build_playoff_data_from_team_games,
    build_playoff_bracket,
    build_team_identity,
    format_team_display_name,
    is_completed_playoff_bracket,
)


def mysql_get_teams_query():
    """Return (columns, rows) for MySQL NBA regular-season teams."""
    conn = connect_mysql()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            t.team_key AS id,
            t.team_tricode AS tricode,
            t.team_city AS city,
            t.team_name AS name
        FROM dim_team AS t
        WHERE EXISTS (
            SELECT 1
            FROM fact_player_game_stats fps
            JOIN dim_game g ON g.game_key = fps.game_key
            WHERE fps.team_key = t.team_key
              AND g.game_type = 'regular_season'
        )
        ORDER BY t.team_name ASC
        """
    )
    rows = []
    for row in cursor.fetchall():
        team_id, tricode, city, name = row
        rows.append(
            {
                "id": team_id,
                "tricode": tricode,
                "name": format_team_display_name(city, name),
                "years": [],
                "top_scorer": "Coming soon",
                "top_assist": "Coming soon",
            }
        )

    cursor.close()
    conn.close()
    return ["id", "tricode", "name", "years", "top_scorer", "top_assist"], rows


def mysql_get_other_teams_query():
    """Return (columns, rows) for non-NBA-regular-season teams."""
    conn = connect_mysql()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            t.team_key AS id,
            t.team_tricode AS tricode,
            t.team_city AS city,
            t.team_name AS name
        FROM dim_team AS t
        WHERE NOT EXISTS (
            SELECT 1
            FROM fact_player_game_stats fps
            JOIN dim_game g ON g.game_key = fps.game_key
            WHERE fps.team_key = t.team_key
              AND g.game_type = 'regular_season'
        )
        ORDER BY t.team_name ASC
        """
    )

    rows = []
    for row in cursor.fetchall():
        team_id, tricode, city, name = row
        rows.append(
            {
                "id": team_id,
                "tricode": tricode,
                "name": format_team_display_name(city, name),
                "years": [],
                "top_scorer": "Coming soon",
                "top_assist": "Coming soon",
            }
        )

    cursor.close()
    conn.close()
    return ["id", "tricode", "name", "years", "top_scorer", "top_assist"], rows


def mysql_get_other_teams_count() -> int:
    return len(mysql_get_other_teams_query()[1])


def mysql_get_team_detail_query(team_id: int) -> dict[str, object] | None:
    conn = connect_mysql()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            t.team_key AS id,
            t.team_tricode AS tricode,
            t.team_city AS city,
            t.team_name AS name,
            COUNT(DISTINCT fps.game_key) AS games_count,
            COUNT(DISTINCT fps.player_key) AS players_count,
            COALESCE(SUM(fps.points), 0) AS total_points,
            COALESCE(
                GROUP_CONCAT(DISTINCT d.year_num ORDER BY d.year_num SEPARATOR ','),
                ''
            ) AS years_csv
        FROM dim_team AS t
        LEFT JOIN fact_player_game_stats fps ON fps.team_key = t.team_key
        LEFT JOIN dim_date d ON d.date_key = fps.date_key
        WHERE t.team_key = %s
        GROUP BY t.team_key, t.team_tricode, t.team_city, t.team_name
        """,
        (team_id,),
    )
    team_row = cursor.fetchone()
    if team_row is None:
        cursor.close()
        conn.close()
        return None

    cursor.execute(
        """
        SELECT p.display_name
        FROM fact_player_game_stats fps
        JOIN dim_player p ON p.player_key = fps.player_key
        WHERE fps.team_key = %s
        GROUP BY p.player_key, p.display_name
        ORDER BY SUM(fps.points) DESC, p.display_name ASC
        LIMIT 1
        """,
        (team_id,),
    )
    top_scorer_row = cursor.fetchone()

    cursor.execute(
        """
        SELECT p.display_name
        FROM fact_player_game_stats fps
        JOIN dim_player p ON p.player_key = fps.player_key
        WHERE fps.team_key = %s
        GROUP BY p.player_key, p.display_name
        ORDER BY SUM(fps.assists) DESC, p.display_name ASC
        LIMIT 1
        """,
        (team_id,),
    )
    top_assist_row = cursor.fetchone()

    cursor.close()
    conn.close()

    detail_id, tricode, city, name, games_count, players_count, total_points, years_csv = team_row
    return {
        "id": detail_id,
        "tricode": tricode,
        "city": city,
        "name": name,
        "full_name": format_team_display_name(city, name),
        "games_count": games_count,
        "players_count": players_count,
        "total_points": total_points,
        "years": [year for year in years_csv.split(",") if year],
        "top_scorer": top_scorer_row[0] if top_scorer_row else "No data",
        "top_assist": top_assist_row[0] if top_assist_row else "No data",
    }


def mysql_year_query():
    conn = connect_mysql()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            yearly.season_label,
            yearly.games,
            yearly.teams,
            yearly.total_points,
            ROUND(yearly.total_points / NULLIF(yearly.team_games, 0), 2) AS avg_team_points
        FROM (
            SELECT
                g.season_label AS season_label,
                COUNT(DISTINCT team_game.game_key) AS games,
                COUNT(DISTINCT team_game.team_key) AS teams,
                SUM(team_game.team_points) AS total_points,
                COUNT(*) AS team_games
            FROM (
                SELECT
                    f.game_key,
                    f.team_key,
                    SUM(f.points) AS team_points
                FROM fact_player_game_stats AS f
                JOIN dim_game AS g ON g.game_key = f.game_key
                WHERE g.game_type = 'regular_season'
                GROUP BY f.game_key, f.team_key
            ) AS team_game
            JOIN dim_game AS g ON g.game_key = team_game.game_key
            WHERE g.season_label IS NOT NULL
              AND TRIM(g.season_label) <> ''
            GROUP BY g.season_label
        ) AS yearly
        ORDER BY yearly.season_label DESC
        """
    )

    columns = [description[0] for description in cursor.description]
    rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

    cursor.close()
    conn.close()
    return columns, rows


def mysql_get_season_detail_query(season_label: str) -> dict[str, object] | None:
    def build_leader(row: dict[str, object]) -> dict[str, object]:
        return {
            "player_name": row["player_name"],
            "team_tricode": row["team_tricode"],
            "total": row["total"],
            "per_game": row["per_game"],
        }

    conn = connect_mysql()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            WITH reg_team_games AS (
                SELECT
                    g.game_key,
                    f.team_key,
                    SUM(f.points) AS team_points
                FROM dim_game AS g
                JOIN fact_player_game_stats AS f ON f.game_key = g.game_key
                WHERE g.game_type = 'regular_season'
                  AND g.season_label = %s
                GROUP BY g.game_key, f.team_key
            )
            SELECT
                %s AS season_label,
                COUNT(DISTINCT game_key) AS games,
                COUNT(DISTINCT team_key) AS teams,
                COALESCE(SUM(team_points), 0) AS total_points,
                ROUND(COALESCE(SUM(team_points), 0) / NULLIF(COUNT(*), 0), 2) AS avg_team_points
            FROM reg_team_games
            """,
            (season_label, season_label),
        )
        summary_row = cursor.fetchone()
        if summary_row is None or summary_row["games"] == 0:
            return None

        cursor.execute(
            """
            WITH reg_team_games AS (
                SELECT
                    g.game_key,
                    f.team_key,
                    SUM(f.points) AS team_points
                FROM dim_game AS g
                JOIN fact_player_game_stats AS f ON f.game_key = g.game_key
                WHERE g.game_type = 'regular_season'
                  AND g.season_label = %s
                GROUP BY g.game_key, f.team_key
            )
            SELECT
                t.team_key AS id,
                t.team_tricode AS tricode,
                t.team_city AS city,
                t.team_name AS name,
                SUM(CASE WHEN team_game.team_points > opponent_game.team_points THEN 1 ELSE 0 END) AS wins,
                SUM(CASE WHEN team_game.team_points < opponent_game.team_points THEN 1 ELSE 0 END) AS losses,
                ROUND(AVG(team_game.team_points), 2) AS points_for,
                ROUND(AVG(opponent_game.team_points), 2) AS points_against
            FROM reg_team_games AS team_game
            JOIN reg_team_games AS opponent_game
              ON opponent_game.game_key = team_game.game_key
             AND opponent_game.team_key <> team_game.team_key
            JOIN dim_team AS t ON t.team_key = team_game.team_key
            GROUP BY t.team_key, t.team_tricode, t.team_city, t.team_name
            ORDER BY wins DESC, losses ASC, points_for DESC, t.team_name ASC
            """,
            (season_label,),
        )
        team_rows = [
            {
                "id": row["id"],
                "tricode": row["tricode"],
                "name": format_team_display_name(row["city"], row["name"]),
                "wins": row["wins"],
                "losses": row["losses"],
                "record": f'{row["wins"]}-{row["losses"]}',
                "points_for": row["points_for"],
                "points_against": row["points_against"],
            }
            for row in cursor.fetchall()
        ]

        cursor.execute(
            """
            WITH player_totals AS (
                SELECT
                    p.display_name,
                    t.team_tricode,
                    SUM(f.points) AS total_points,
                    ROUND(SUM(f.points) / NULLIF(COUNT(DISTINCT f.game_key), 0), 2) AS points_per_game,
                    SUM(f.assists) AS total_assists,
                    ROUND(SUM(f.assists) / NULLIF(COUNT(DISTINCT f.game_key), 0), 2) AS assists_per_game,
                    SUM(f.rebounds_total) AS total_rebounds,
                    ROUND(SUM(f.rebounds_total) / NULLIF(COUNT(DISTINCT f.game_key), 0), 2) AS rebounds_per_game
                FROM dim_game AS g
                JOIN fact_player_game_stats AS f ON f.game_key = g.game_key
                JOIN dim_player AS p ON p.player_key = f.player_key
                JOIN dim_team AS t ON t.team_key = f.team_key
                WHERE g.game_type = 'regular_season'
                  AND g.season_label = %s
                GROUP BY p.player_key, p.display_name, t.team_tricode
            ),
            ranked AS (
                SELECT
                    category,
                    player_name,
                    team_tricode,
                    total,
                    per_game,
                    ROW_NUMBER() OVER (
                        PARTITION BY category
                        ORDER BY total DESC, per_game DESC, player_name ASC
                    ) AS rn
                FROM (
                    SELECT 'points' AS category, display_name AS player_name, team_tricode, total_points AS total, points_per_game AS per_game FROM player_totals
                    UNION ALL
                    SELECT 'assists' AS category, display_name AS player_name, team_tricode, total_assists AS total, assists_per_game AS per_game FROM player_totals
                    UNION ALL
                    SELECT 'rebounds' AS category, display_name AS player_name, team_tricode, total_rebounds AS total, rebounds_per_game AS per_game FROM player_totals
                ) AS leaderboard
            )
            SELECT
                category,
                player_name,
                team_tricode,
                total,
                per_game
            FROM ranked
            WHERE rn <= 10
            ORDER BY category, rn
            """,
            (season_label,),
        )
        leaders = {"points": [], "assists": [], "rebounds": []}
        for row in cursor.fetchall():
            leaders[row["category"]].append(build_leader(row))

        cursor.execute(
            """
            SELECT
                g.source_game_id AS source_game_id,
                g.game_date_key AS game_date_key,
                t.team_key AS team_id,
                t.team_tricode AS team_tricode,
                t.team_city AS team_city,
                t.team_name AS team_name,
                SUM(f.points) AS team_points
            FROM dim_game AS g
            JOIN fact_player_game_stats AS f ON f.game_key = g.game_key
            JOIN dim_team AS t ON t.team_key = f.team_key
            WHERE g.game_type = 'playoffs'
              AND g.season_label = %s
            GROUP BY
                g.source_game_id,
                g.game_date_key,
                t.team_key,
                t.team_tricode,
                t.team_city,
                t.team_name
            ORDER BY g.game_date_key ASC, g.source_game_id ASC, t.team_key ASC
            """,
            (season_label,),
        )
        playoff_team_game_rows = cursor.fetchall()
        playoff_series_rows, playoff_winner = build_playoff_data_from_team_games(playoff_team_game_rows)

        playoff_bracket = build_playoff_bracket(playoff_series_rows)
        playoffs_complete = is_completed_playoff_bracket(playoff_bracket)

        return {
            "season_label": summary_row["season_label"],
            "games": summary_row["games"],
            "teams": summary_row["teams"],
            "total_points": summary_row["total_points"],
            "avg_team_points": summary_row["avg_team_points"],
            "team_records": team_rows,
            "top_scorers": leaders["points"],
            "top_assists": leaders["assists"],
            "top_rebounds": leaders["rebounds"],
            "playoff_winner": playoff_winner,
            "playoff_series": playoff_series_rows,
            "playoffs_complete": playoffs_complete,
            "playoff_bracket": playoff_bracket if playoff_series_rows else None,
        }
    finally:
        cursor.close()
        conn.close()


def mysql_get_missing_season_games_query():
    conn = connect_mysql()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            g.game_key AS game_key,
            g.source_game_id AS source_game_id,
            d.full_date AS game_date,
            COALESCE(home.team_tricode, '?') AS home_team,
            COALESCE(away.team_tricode, '?') AS away_team,
            COUNT(DISTINCT fps.team_key) AS teams_in_stats,
            COUNT(DISTINCT fps.player_key) AS players_in_stats
        FROM dim_game AS g
        LEFT JOIN dim_date AS d ON d.date_key = g.game_date_key
        LEFT JOIN dim_team AS home ON home.team_key = g.home_team_key
        LEFT JOIN dim_team AS away ON away.team_key = g.away_team_key
        LEFT JOIN fact_player_game_stats AS fps ON fps.game_key = g.game_key
        WHERE g.game_type = 'regular_season'
          AND (g.season_label IS NULL OR TRIM(g.season_label) = '')
        GROUP BY
            g.game_key,
            g.source_game_id,
            d.full_date,
            home.team_tricode,
            away.team_tricode
        ORDER BY d.full_date DESC, g.source_game_id DESC
        """
    )

    columns = [description[0] for description in cursor.description]
    rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

    cursor.close()
    conn.close()
    return columns, rows


def mysql_get_missing_season_games_count() -> int:
    return len(mysql_get_missing_season_games_query()[1])
