"""Umbrella frontend for the Basketball Data Warehouse."""

from __future__ import annotations

import os
import sys
from functools import lru_cache

from dotenv import load_dotenv
from flask import Flask, render_template, abort

# Ensure project root is on the path so we can import src.clients
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

load_dotenv()

app = Flask(__name__)

VALID_DBS = {"mysql", "mongodb", "neo4j"}
PLAYOFF_ROUND_NAMES = {
    1: "First Round",
    2: "Conference Semifinals",
    3: "Conference Finals",
    4: "NBA Finals",
}
TEAM_CONFERENCES = {
    "ATL": "East",
    "BKN": "East",
    "BOS": "East",
    "CHA": "East",
    "CHI": "East",
    "CLE": "East",
    "DET": "East",
    "IND": "East",
    "MIA": "East",
    "MIL": "East",
    "NYK": "East",
    "ORL": "East",
    "PHI": "East",
    "TOR": "East",
    "WAS": "East",
    "DAL": "West",
    "DEN": "West",
    "GSW": "West",
    "HOU": "West",
    "LAC": "West",
    "LAL": "West",
    "MEM": "West",
    "MIN": "West",
    "NOP": "West",
    "OKC": "West",
    "PHX": "West",
    "POR": "West",
    "SAC": "West",
    "SAS": "West",
    "UTA": "West",
}


# ---------------------------------------------------------------------------
# Query functions — fill in your own queries here
# ---------------------------------------------------------------------------
def format_team_display_name(team_city: str | None, team_name: str | None) -> str:
    city = (team_city or "").strip()
    name = (team_name or "").strip()

    if not city:
        return name
    if not name:
        return city

    city_lower = city.lower()
    name_lower = name.lower()

    if name_lower == city_lower:
        return name
    if name_lower.startswith(city_lower + " "):
        return name
    if city_lower in name_lower:
        return name

    return f"{city} {name}"


def build_team_identity(team_id: int, tricode: str, city: str | None, name: str | None) -> dict[str, object]:
    return {
        "id": team_id,
        "tricode": tricode,
        "name": format_team_display_name(city, name),
    }


def summarize_season_team_games(season_label: str, team_game_rows: list[dict[str, object]]) -> dict[str, object] | None:
    if not team_game_rows:
        return None

    total_points = sum(int(row["team_points"]) for row in team_game_rows)
    return {
        "season_label": season_label,
        "games": len({str(row["source_game_id"]) for row in team_game_rows}),
        "teams": len({int(row["team_id"]) for row in team_game_rows}),
        "total_points": total_points,
        "avg_team_points": round(total_points / len(team_game_rows), 2) if team_game_rows else 0,
    }


def build_team_records_from_team_games(team_game_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    games: dict[str, list[dict[str, object]]] = {}
    team_totals: dict[int, dict[str, object]] = {}

    for row in team_game_rows:
        games.setdefault(str(row["source_game_id"]), []).append(row)

    for game_rows in games.values():
        if len(game_rows) != 2:
            continue

        first, second = game_rows
        for team_row, opponent_row in ((first, second), (second, first)):
            team_id = int(team_row["team_id"])
            totals = team_totals.setdefault(
                team_id,
                {
                    **build_team_identity(
                        team_id,
                        str(team_row["team_tricode"]),
                        team_row.get("team_city"),
                        team_row.get("team_name"),
                    ),
                    "wins": 0,
                    "losses": 0,
                    "points_for_total": 0,
                    "points_against_total": 0,
                    "games": 0,
                },
            )
            team_points = int(team_row["team_points"])
            opponent_points = int(opponent_row["team_points"])
            totals["wins"] += int(team_points > opponent_points)
            totals["losses"] += int(team_points < opponent_points)
            totals["points_for_total"] += team_points
            totals["points_against_total"] += opponent_points
            totals["games"] += 1

    rows = []
    for totals in team_totals.values():
        games_played = int(totals["games"]) or 1
        wins = int(totals["wins"])
        losses = int(totals["losses"])
        rows.append(
            {
                "id": totals["id"],
                "tricode": totals["tricode"],
                "name": totals["name"],
                "wins": wins,
                "losses": losses,
                "record": f"{wins}-{losses}",
                "points_for": round(int(totals["points_for_total"]) / games_played, 2),
                "points_against": round(int(totals["points_against_total"]) / games_played, 2),
            }
        )

    rows.sort(key=lambda row: (-row["wins"], row["losses"], -row["points_for"], row["name"]))
    return rows


def build_playoff_data_from_team_games(playoff_team_game_rows: list[dict[str, object]]) -> tuple[list[dict[str, object]], dict[str, object] | None]:
    if not playoff_team_game_rows:
        return [], None

    games: dict[str, list[dict[str, object]]] = {}
    series_map: dict[str, dict[str, object]] = {}
    latest_source_game_id = max(str(row["source_game_id"]) for row in playoff_team_game_rows)

    for row in playoff_team_game_rows:
        source_game_id = str(row["source_game_id"])
        games.setdefault(source_game_id, []).append(row)

    for source_game_id, game_rows in games.items():
        if len(game_rows) != 2:
            continue

        round_num = int(source_game_id[7])
        series_key = source_game_id[:9]
        first, second = game_rows
        series = series_map.setdefault(
            series_key,
            {
                "round_num": round_num,
                "series_key": series_key,
                "teams": {
                    int(first["team_id"]): {
                        **build_team_identity(
                            int(first["team_id"]),
                            str(first["team_tricode"]),
                            first.get("team_city"),
                            first.get("team_name"),
                        ),
                        "wins": 0,
                    },
                    int(second["team_id"]): {
                        **build_team_identity(
                            int(second["team_id"]),
                            str(second["team_tricode"]),
                            second.get("team_city"),
                            second.get("team_name"),
                        ),
                        "wins": 0,
                    },
                },
            },
        )
        first_points = int(first["team_points"])
        second_points = int(second["team_points"])
        if first_points > second_points:
            series["teams"][int(first["team_id"])]["wins"] += 1
        elif second_points > first_points:
            series["teams"][int(second["team_id"])]["wins"] += 1

    playoff_series_rows = []
    playoff_winner = None
    latest_rows = games.get(latest_source_game_id, [])
    if len(latest_rows) == 2:
        latest_winner_row = max(latest_rows, key=lambda row: int(row["team_points"]))
        playoff_winner = {
            **build_team_identity(
                int(latest_winner_row["team_id"]),
                str(latest_winner_row["team_tricode"]),
                latest_winner_row.get("team_city"),
                latest_winner_row.get("team_name"),
            ),
            "source_game_id": latest_source_game_id,
            "game_date_key": latest_winner_row.get("game_date_key"),
        }

    for series in sorted(series_map.values(), key=lambda item: (int(item["round_num"]), str(item["series_key"]))):
        teams = sorted(series["teams"].values(), key=lambda team: (team["id"], team["name"]))
        if len(teams) != 2:
            continue
        playoff_series_rows.append(
            {
                "round_num": series["round_num"],
                "round_name": PLAYOFF_ROUND_NAMES.get(series["round_num"], f'Round {series["round_num"]}'),
                "series_key": series["series_key"],
                "team_one": teams[0],
                "team_two": teams[1],
            }
        )

    return playoff_series_rows, playoff_winner


def build_playoff_bracket(playoff_series: list[dict[str, object]]) -> dict[str, object]:
    left_columns = [
        {"title": "First Round", "series": []},
        {"title": "Conference Semifinals", "series": []},
        {"title": "Conference Finals", "series": []},
    ]
    right_columns = [
        {"title": "Conference Finals", "series": []},
        {"title": "Conference Semifinals", "series": []},
        {"title": "First Round", "series": []},
    ]
    finals_series = []

    for series in playoff_series:
        round_num = int(series["round_num"])
        if round_num == 4:
            finals_series.append(series)
            continue

        conference = TEAM_CONFERENCES.get(str(series["team_one"]["tricode"]))
        if conference == "West":
            left_columns[round_num - 1]["series"].append(series)
        elif conference == "East":
            right_columns[3 - round_num]["series"].append(series)

    for column in left_columns + right_columns:
        column["series"].sort(key=lambda item: item["series_key"])

    finals_series.sort(key=lambda item: item["series_key"])
    return {
        "left_label": "West",
        "right_label": "East",
        "left_columns": left_columns,
        "right_columns": right_columns,
        "finals": finals_series[0] if finals_series else None,
    }


def is_completed_playoff_bracket(playoff_bracket: dict[str, object] | None) -> bool:
    if not playoff_bracket:
        return False

    finals = playoff_bracket.get("finals")
    if not isinstance(finals, dict):
        return False

    team_one = finals.get("team_one")
    team_two = finals.get("team_two")
    if not isinstance(team_one, dict) or not isinstance(team_two, dict):
        return False

    team_one_wins = int(team_one.get("wins", 0))
    team_two_wins = int(team_two.get("wins", 0))
    return team_one_wins == 4 or team_two_wins == 4


def build_season_payload(
    season_label: str,
    team_game_rows: list[dict[str, object]],
    leaders: dict[str, list[dict[str, object]]],
    playoff_team_game_rows: list[dict[str, object]] | None = None,
) -> dict[str, object] | None:
    summary = summarize_season_team_games(season_label, team_game_rows)
    if summary is None:
        return None

    playoff_series_rows, playoff_winner = build_playoff_data_from_team_games(playoff_team_game_rows or [])
    playoff_bracket = build_playoff_bracket(playoff_series_rows)
    playoffs_complete = is_completed_playoff_bracket(playoff_bracket)

    return {
        **summary,
        "team_records": build_team_records_from_team_games(team_game_rows),
        "top_scorers": leaders.get("points", []),
        "top_assists": leaders.get("assists", []),
        "top_rebounds": leaders.get("rebounds", []),
        "playoff_winner": playoff_winner,
        "playoff_series": playoff_series_rows,
        "playoffs_complete": playoffs_complete,
        "playoff_bracket": playoff_bracket if playoffs_complete else None,
    }


def mysql_get_teams_query():
    """Return (columns, rows) for MySQL NBA regular-season teams."""
    from src.clients.mysql_client import connect_mysql

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
              AND g.source_game_id LIKE '002%%'
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
    from src.clients.mysql_client import connect_mysql

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
              AND g.source_game_id LIKE '002%%'
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
    """Return count of teams outside the NBA regular-season set."""
    return len(mysql_get_other_teams_query()[1])


def mysql_get_team_detail_query(team_id: int) -> dict[str, object] | None:
    """Return one MySQL team detail payload."""
    from src.clients.mysql_client import connect_mysql

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


@lru_cache(maxsize=32)
def mysql_year_query():
    """Return (columns, rows) for MySQL year statistics."""
    from src.clients.mysql_client import connect_mysql

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
                WHERE g.source_game_id LIKE '002%%'
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


@lru_cache(maxsize=32)
def mysql_get_season_detail_query(season_label: str) -> dict[str, object] | None:
    """Return one MySQL season detail payload."""
    from src.clients.mysql_client import connect_mysql

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
                WHERE g.source_game_id LIKE '002%%'
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
                WHERE g.source_game_id LIKE '002%%'
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
                WHERE g.source_game_id LIKE '002%%'
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
            WITH playoff_team_games AS (
                SELECT
                    g.game_key,
                    g.source_game_id,
                    g.game_date_key,
                    SUBSTRING(g.source_game_id, 1, 9) AS series_key,
                    CAST(SUBSTRING(g.source_game_id, 8, 1) AS UNSIGNED) AS round_num,
                    f.team_key,
                    SUM(f.points) AS team_points
                FROM dim_game AS g
                JOIN fact_player_game_stats AS f ON f.game_key = g.game_key
                WHERE g.source_game_id LIKE '004%%'
                  AND g.season_label = %s
                GROUP BY
                    g.game_key,
                    g.source_game_id,
                    g.game_date_key,
                    SUBSTRING(g.source_game_id, 1, 9),
                    CAST(SUBSTRING(g.source_game_id, 8, 1) AS UNSIGNED),
                    f.team_key
            ),
            series_team_wins AS (
                SELECT
                    team_game.series_key,
                    team_game.round_num,
                    team_game.team_key,
                    SUM(CASE WHEN team_game.team_points > opponent_game.team_points THEN 1 ELSE 0 END) AS series_wins
                FROM playoff_team_games AS team_game
                JOIN playoff_team_games AS opponent_game
                  ON opponent_game.game_key = team_game.game_key
                 AND opponent_game.team_key <> team_game.team_key
                GROUP BY team_game.series_key, team_game.round_num, team_game.team_key
            ),
            series_pairs AS (
                SELECT
                    series_a.round_num,
                    series_a.series_key,
                    series_a.team_key AS team_one_id,
                    series_a.series_wins AS team_one_wins,
                    series_b.team_key AS team_two_id,
                    series_b.series_wins AS team_two_wins
                FROM series_team_wins AS series_a
                JOIN series_team_wins AS series_b
                  ON series_b.series_key = series_a.series_key
                 AND series_b.team_key > series_a.team_key
            ),
            latest_playoff_game AS (
                SELECT
                    team_game.game_key,
                    team_game.source_game_id,
                    team_game.game_date_key
                FROM playoff_team_games AS team_game
                GROUP BY team_game.game_key, team_game.source_game_id, team_game.game_date_key
                ORDER BY team_game.game_date_key DESC, team_game.source_game_id DESC
                LIMIT 1
            ),
            latest_playoff_winner AS (
            SELECT
                    team_game.team_key,
                    latest_playoff_game.source_game_id,
                    latest_playoff_game.game_date_key,
                    ROW_NUMBER() OVER (
                        ORDER BY team_game.team_points DESC, team_game.team_key ASC
                    ) AS rn
                FROM latest_playoff_game
                JOIN playoff_team_games AS team_game
                  ON team_game.game_key = latest_playoff_game.game_key
            )
            SELECT
                series_pairs.round_num,
                series_pairs.series_key,
                series_pairs.team_one_id,
                team_one.team_tricode AS team_one_tricode,
                team_one.team_city AS team_one_city,
                team_one.team_name AS team_one_name,
                series_pairs.team_one_wins,
                series_pairs.team_two_id,
                team_two.team_tricode AS team_two_tricode,
                team_two.team_city AS team_two_city,
                team_two.team_name AS team_two_name,
                series_pairs.team_two_wins,
                latest_playoff_winner.team_key AS playoff_winner_team_key,
                winner_team.team_tricode AS playoff_winner_tricode,
                winner_team.team_city AS playoff_winner_city,
                winner_team.team_name AS playoff_winner_name,
                latest_playoff_winner.source_game_id AS playoff_winner_source_game_id,
                latest_playoff_winner.game_date_key AS playoff_winner_game_date_key
            FROM series_pairs
            JOIN dim_team AS team_one ON team_one.team_key = series_pairs.team_one_id
            JOIN dim_team AS team_two ON team_two.team_key = series_pairs.team_two_id
            LEFT JOIN latest_playoff_winner
              ON latest_playoff_winner.rn = 1
            LEFT JOIN dim_team AS winner_team
              ON winner_team.team_key = latest_playoff_winner.team_key
            ORDER BY series_pairs.round_num ASC, series_pairs.series_key ASC
            """,
            (season_label,),
        )
        playoff_series_rows = []
        playoff_rows = cursor.fetchall()
        playoff_winner = None
        for row in playoff_rows:
            playoff_series_rows.append(
                {
                    "round_num": row["round_num"],
                    "round_name": PLAYOFF_ROUND_NAMES.get(row["round_num"], f'Round {row["round_num"]}'),
                    "series_key": row["series_key"],
                    "team_one": {
                        **build_team_identity(
                            row["team_one_id"],
                            row["team_one_tricode"],
                            row["team_one_city"],
                            row["team_one_name"],
                        ),
                        "wins": row["team_one_wins"],
                    },
                    "team_two": {
                        **build_team_identity(
                            row["team_two_id"],
                            row["team_two_tricode"],
                            row["team_two_city"],
                            row["team_two_name"],
                        ),
                        "wins": row["team_two_wins"],
                    },
                }
            )
            if playoff_winner is None and row["playoff_winner_team_key"] is not None:
                playoff_winner = {
                    **build_team_identity(
                        row["playoff_winner_team_key"],
                        row["playoff_winner_tricode"],
                        row["playoff_winner_city"],
                        row["playoff_winner_name"],
                    ),
                    "source_game_id": row["playoff_winner_source_game_id"],
                    "game_date_key": row["playoff_winner_game_date_key"],
                }

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
            "playoff_bracket": playoff_bracket if playoffs_complete else None,
        }
    finally:
        cursor.close()
        conn.close()


def mysql_get_missing_season_games_query():
    """Return games missing a MySQL season label."""
    from src.clients.mysql_client import connect_mysql

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
        WHERE g.source_game_id LIKE '002%%'
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
    """Return count of games missing a MySQL season label."""
    return len(mysql_get_missing_season_games_query()[1])


def mongodb_team_query():
    """Return (columns, rows) for MongoDB team statistics."""
    from src.clients.mongodb_client import connect_mongodb

    db = connect_mongodb()

    # Base team list for NBA regular-season teams
    team_pipeline = [
        {
            "$match": {
                "sourceGameId": {"$regex": "^002"},
            }
        },
        {
            "$group": {
                "_id": {
                    "id": "$team.sourceTeamId",
                    "tricode": "$team.teamTricode",
                    "city": "$team.teamCity",
                    "name": "$team.teamName",
                },
                "years": {"$addToSet": {"$year": "$gameDate"}},
            }
        },
        {
            "$project": {
                "_id": 0,
                "id": "$_id.id",
                "tricode": "$_id.tricode",
                "city": "$_id.city",
                "name_raw": "$_id.name",
                "years": "$years",
            }
        },
        {"$sort": {"name_raw": 1}},
    ]

    # Top scorer per team
    top_scorer_pipeline = [
        {
            "$match": {
                "sourceGameId": {"$regex": "^002"},
            }
        },
        {
            "$group": {
                "_id": {
                    "teamId": "$team.sourceTeamId",
                    "playerId": "$player.sourcePersonId",
                    "playerName": "$player.displayName",
                },
                "total_points": {"$sum": "$stats.points"},
            }
        },
        {
            "$sort": {
                "_id.teamId": 1,
                "total_points": -1,
                "_id.playerName": 1,
            }
        },
        {
            "$group": {
                "_id": "$_id.teamId",
                "top_scorer": {"$first": "$_id.playerName"},
            }
        },
    ]

    # Top assister per team
    top_assist_pipeline = [
        {
            "$match": {
                "sourceGameId": {"$regex": "^002"},
            }
        },
        {
            "$group": {
                "_id": {
                    "teamId": "$team.sourceTeamId",
                    "playerId": "$player.sourcePersonId",
                    "playerName": "$player.displayName",
                },
                "total_assists": {"$sum": "$stats.assists"},
            }
        },
        {
            "$sort": {
                "_id.teamId": 1,
                "total_assists": -1,
                "_id.playerName": 1,
            }
        },
        {
            "$group": {
                "_id": "$_id.teamId",
                "top_assist": {"$first": "$_id.playerName"},
            }
        },
    ]

    team_docs = list(db.player_game_stats.aggregate(team_pipeline))
    scorer_docs = list(db.player_game_stats.aggregate(top_scorer_pipeline))
    assist_docs = list(db.player_game_stats.aggregate(top_assist_pipeline))

    scorer_map = {int(doc["_id"]): doc["top_scorer"] for doc in scorer_docs}
    assist_map = {int(doc["_id"]): doc["top_assist"] for doc in assist_docs}

    rows = []
    for doc in team_docs:
        team_id = int(doc["id"])
        city = doc.get("city")
        name_raw = doc.get("name_raw")
        years = sorted(
            [int(year) for year in doc.get("years", []) if year is not None]
        )

        rows.append(
            {
                "id": team_id,
                "tricode": doc.get("tricode", ""),
                "name": format_team_display_name(city, name_raw),
                "years": years,
                "top_scorer": scorer_map.get(team_id, "No data"),
                "top_assist": assist_map.get(team_id, "No data"),
            }
        )

    rows.sort(key=lambda row: row["name"])
    columns = ["id", "tricode", "name", "years", "top_scorer", "top_assist"]
    return columns, rows


def mongodb_year_query():
    """Return (columns, rows) for MongoDB year statistics."""
    from src.clients.mongodb_client import connect_mongodb

    db = connect_mongodb()
    pipeline = [
        {
            "$match": {
                "sourceGameId": {"$regex": "^002"},
                "seasonLabel": {"$nin": [None, ""]},
            }
        },
        {
            "$group": {
                "_id": {
                    "seasonLabel": "$seasonLabel",
                    "sourceGameId": "$sourceGameId",
                    "teamId": "$team.sourceTeamId",
                },
                "teamPoints": {"$sum": "$stats.points"},
            }
        },
        {
            "$group": {
                "_id": "$_id.seasonLabel",
                "games": {"$addToSet": "$_id.sourceGameId"},
                "teams": {"$addToSet": "$_id.teamId"},
                "total_points": {"$sum": "$teamPoints"},
                "team_games": {"$sum": 1},
            }
        },
        {
            "$project": {
                "_id": 0,
                "season_label": "$_id",
                "games": {"$size": "$games"},
                "teams": {"$size": "$teams"},
                "total_points": 1,
                "avg_team_points": {"$round": [{"$divide": ["$total_points", "$team_games"]}, 2]},
            }
        },
        {"$sort": {"season_label": -1}},
    ]
    rows = list(db.player_game_stats.aggregate(pipeline))
    columns = ["season_label", "games", "teams", "total_points", "avg_team_points"]

    return columns, rows


@lru_cache(maxsize=32)
def mongodb_get_season_detail_query(season_label: str) -> dict[str, object] | None:
    """Return one MongoDB season detail payload."""
    from src.clients.mongodb_client import connect_mongodb

    db = connect_mongodb()

    regular_team_game_pipeline = [
        {"$match": {"sourceGameId": {"$regex": "^002"}, "seasonLabel": season_label}},
        {
            "$group": {
                "_id": {
                    "sourceGameId": "$sourceGameId",
                    "teamId": "$team.sourceTeamId",
                },
                "team_points": {"$sum": "$stats.points"},
                "team_tricode": {"$first": "$team.teamTricode"},
                "team_city": {"$first": "$team.teamCity"},
                "team_name": {"$first": "$team.teamName"},
            }
        },
        {
            "$project": {
                "_id": 0,
                "source_game_id": "$_id.sourceGameId",
                "team_id": "$_id.teamId",
                "team_points": "$team_points",
                "team_tricode": "$team_tricode",
                "team_city": "$team_city",
                "team_name": "$team_name",
            }
        },
    ]
    team_game_rows = list(db.player_game_stats.aggregate(regular_team_game_pipeline))

    leaderboard_pipeline = [
        {"$match": {"sourceGameId": {"$regex": "^002"}, "seasonLabel": season_label}},
        {
            "$group": {
                "_id": {
                    "playerId": "$player.sourcePersonId",
                    "playerName": "$player.displayName",
                    "teamTricode": "$team.teamTricode",
                },
                "games": {"$addToSet": "$sourceGameId"},
                "points": {"$sum": "$stats.points"},
                "assists": {"$sum": "$stats.assists"},
                "rebounds": {"$sum": "$stats.reboundsTotal"},
            }
        },
        {
            "$project": {
                "_id": 0,
                "player_name": "$_id.playerName",
                "team_tricode": "$_id.teamTricode",
                "games_played": {"$size": "$games"},
                "points": 1,
                "assists": 1,
                "rebounds": 1,
            }
        },
    ]
    leaderboard_rows = list(db.player_game_stats.aggregate(leaderboard_pipeline))
    leaders = {"points": [], "assists": [], "rebounds": []}
    stat_map = {
        "points": ("points", "points"),
        "assists": ("assists", "assists"),
        "rebounds": ("rebounds", "rebounds"),
    }
    for key, (field_name, output_key) in stat_map.items():
        sorted_rows = sorted(
            leaderboard_rows,
            key=lambda row: (
                -int(row[field_name]),
                -(float(row[field_name]) / max(int(row["games_played"]), 1)),
                str(row["player_name"]),
            ),
        )[:10]
        leaders[output_key] = [
            {
                "player_name": row["player_name"],
                "team_tricode": row["team_tricode"],
                "total": int(row[field_name]),
                "per_game": round(float(row[field_name]) / max(int(row["games_played"]), 1), 2),
            }
            for row in sorted_rows
        ]

    playoff_team_game_pipeline = [
        {"$match": {"sourceGameId": {"$regex": "^004"}, "seasonLabel": season_label}},
        {
            "$group": {
                "_id": {
                    "sourceGameId": "$sourceGameId",
                    "teamId": "$team.sourceTeamId",
                },
                "team_points": {"$sum": "$stats.points"},
                "team_tricode": {"$first": "$team.teamTricode"},
                "team_city": {"$first": "$team.teamCity"},
                "team_name": {"$first": "$team.teamName"},
                "game_date_key": {"$max": "$gameDate"},
            }
        },
        {
            "$project": {
                "_id": 0,
                "source_game_id": "$_id.sourceGameId",
                "team_id": "$_id.teamId",
                "team_points": "$team_points",
                "team_tricode": "$team_tricode",
                "team_city": "$team_city",
                "team_name": "$team_name",
                "game_date_key": "$game_date_key",
            }
        },
    ]
    playoff_team_game_rows = list(db.player_game_stats.aggregate(playoff_team_game_pipeline))

    return build_season_payload(season_label, team_game_rows, leaders, playoff_team_game_rows)


def neo4j_team_query():
    """Return (columns, rows) for Neo4j team statistics."""
    from src.clients.neo4j_client import connect_neo4j

    driver = connect_neo4j()

    # TODO: write your Neo4j team Cypher query here
    # Example:
    # with driver.session() as session:
    #     result = session.run("MATCH ... RETURN ...")
    #     columns = result.keys()
    #     rows = [record.values() for record in result]

    columns, rows = [], []

    driver.close()
    return columns, rows


def neo4j_year_query():
    """Return (columns, rows) for Neo4j year statistics."""
    from src.clients.neo4j_client import connect_neo4j

    driver = connect_neo4j()
    with driver.session() as session:
        result = session.run(
            """
            MATCH (g:Game)<-[played:PLAYED_IN]-(:Player)
            MATCH (team:Team {sourceTeamId: played.sourceTeamId})
            WHERE g.sourceGameId STARTS WITH '002'
              AND g.seasonLabel IS NOT NULL
              AND trim(g.seasonLabel) <> ''
            WITH g.seasonLabel AS season_label, g.sourceGameId AS source_game_id, team.sourceTeamId AS team_id, sum(played.points) AS team_points
            WITH season_label,
                 collect(DISTINCT source_game_id) AS games,
                 collect(DISTINCT team_id) AS teams,
                 sum(team_points) AS total_points,
                 count(*) AS team_games
            RETURN season_label, size(games) AS games, size(teams) AS teams, total_points,
                   round((toFloat(total_points) / team_games) * 100) / 100.0 AS avg_team_points
            ORDER BY season_label DESC
            """
        )
        rows = [record.data() for record in result]
    driver.close()
    columns = ["season_label", "games", "teams", "total_points", "avg_team_points"]
    return columns, rows


@lru_cache(maxsize=32)
def neo4j_get_season_detail_query(season_label: str) -> dict[str, object] | None:
    """Return one Neo4j season detail payload."""
    from src.clients.neo4j_client import connect_neo4j

    driver = connect_neo4j()
    with driver.session() as session:
        team_game_rows = [
            record.data()
            for record in session.run(
                """
                MATCH (g:Game)<-[played:PLAYED_IN]-(:Player)
                MATCH (team:Team {sourceTeamId: played.sourceTeamId})
                WHERE g.sourceGameId STARTS WITH '002'
                  AND g.seasonLabel = $season_label
                WITH g.sourceGameId AS source_game_id,
                     team.sourceTeamId AS team_id,
                     team.teamTricode AS team_tricode,
                     team.teamCity AS team_city,
                     team.teamName AS team_name,
                     sum(played.points) AS team_points
                RETURN source_game_id, team_id, team_tricode, team_city, team_name, team_points
                """,
                season_label=season_label,
            )
        ]

        leaderboard_rows = [
            record.data()
            for record in session.run(
                """
                MATCH (g:Game)<-[played:PLAYED_IN]-(player:Player)
                MATCH (team:Team {sourceTeamId: played.sourceTeamId})
                WHERE g.sourceGameId STARTS WITH '002'
                  AND g.seasonLabel = $season_label
                RETURN player.displayName AS player_name,
                       team.teamTricode AS team_tricode,
                       count(DISTINCT g.sourceGameId) AS games_played,
                       sum(played.points) AS points,
                       sum(played.assists) AS assists,
                       sum(played.reboundsTotal) AS rebounds
                """,
                season_label=season_label,
            )
        ]

        playoff_team_game_rows = [
            record.data()
            for record in session.run(
                """
                MATCH (g:Game)<-[played:PLAYED_IN]-(:Player)
                MATCH (team:Team {sourceTeamId: played.sourceTeamId})
                WHERE g.sourceGameId STARTS WITH '004'
                  AND g.seasonLabel = $season_label
                OPTIONAL MATCH (g)-[:ON_DATE]->(d:Date)
                WITH g.sourceGameId AS source_game_id,
                     team.sourceTeamId AS team_id,
                     team.teamTricode AS team_tricode,
                     team.teamCity AS team_city,
                     team.teamName AS team_name,
                     d.dateKey AS game_date_key,
                     sum(played.points) AS team_points
                RETURN source_game_id, team_id, team_tricode, team_city, team_name, game_date_key, team_points
                """,
                season_label=season_label,
            )
        ]

    driver.close()

    leaders = {"points": [], "assists": [], "rebounds": []}
    stat_map = {
        "points": ("points", "points"),
        "assists": ("assists", "assists"),
        "rebounds": ("rebounds", "rebounds"),
    }
    for key, (field_name, output_key) in stat_map.items():
        sorted_rows = sorted(
            leaderboard_rows,
            key=lambda row: (
                -int(row[field_name]),
                -(float(row[field_name]) / max(int(row["games_played"]), 1)),
                str(row["player_name"]),
            ),
        )[:10]
        leaders[output_key] = [
            {
                "player_name": row["player_name"],
                "team_tricode": row["team_tricode"],
                "total": int(row[field_name]),
                "per_game": round(float(row[field_name]) / max(int(row["games_played"]), 1), 2),
            }
            for row in sorted_rows
        ]

    return build_season_payload(season_label, team_game_rows, leaders, playoff_team_game_rows)


YEAR_DETAIL_DISPATCH = {
    "mysql": mysql_get_season_detail_query,
    "mongodb": mongodb_get_season_detail_query,
    "neo4j": neo4j_get_season_detail_query,
}


# Dispatch table mapping (db, category) -> query function
QUERY_DISPATCH = {
    ("mysql", "team"): mysql_get_teams_query,
    ("mysql", "year"): mysql_year_query,
    ("mongodb", "team"): mongodb_team_query,
    ("mongodb", "year"): mongodb_year_query,
    ("neo4j", "team"): neo4j_team_query,
    ("neo4j", "year"): neo4j_year_query,
}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/<db>")
def database(db):
    if db not in VALID_DBS:
        abort(404)
    return render_template("database.html", db=db)


@app.route("/<db>/team")
def team(db):
    if db not in VALID_DBS:
        abort(404)
    query_fn = QUERY_DISPATCH[(db, "team")]

    columns, rows = query_fn()
    other_teams_count = mysql_get_other_teams_count() if db == "mysql" else 0
    return render_template(
        "team.html",
        db=db,
        columns=columns,
        rows=rows,
        page_title="NBA Teams",
        page_intro="Browse the 30 NBA teams represented in the regular-season warehouse data.",
        show_other_card=(db == "mysql" and other_teams_count > 0),
        other_teams_count=other_teams_count,
    )


@app.route("/<db>/team/other")
def other_teams(db):
    if db not in VALID_DBS:
        abort(404)
    if db != "mysql":
        abort(404)

    columns, rows = mysql_get_other_teams_query()
    return render_template(
        "team.html",
        db=db,
        columns=columns,
        rows=rows,
        page_title="Other Teams",
        page_intro="Teams that appear in the warehouse but are not part of the NBA regular-season team set.",
        show_other_card=False,
        other_teams_count=0,
    )


@app.route("/<db>/team/<int:team_id>")
def team_detail(db, team_id):
    if db not in VALID_DBS:
        abort(404)
    if db != "mysql":
        abort(404)

    team_data = mysql_get_team_detail_query(team_id)
    if team_data is None:
        abort(404)

    return render_template("team_detail.html", db=db, team=team_data)


@app.route("/<db>/year")
def year(db):
    if db not in VALID_DBS:
        abort(404)
    query_fn = QUERY_DISPATCH[(db, "year")]
    columns, rows = query_fn()
    missing_season_games_count = mysql_get_missing_season_games_count() if db == "mysql" else 0
    return render_template(
        "year.html",
        db=db,
        columns=columns,
        rows=rows,
        missing_season_games_count=missing_season_games_count,
    )


@app.route("/<db>/year/<season_label>")
def year_detail(db, season_label):
    if db not in VALID_DBS:
        abort(404)

    season_data = YEAR_DETAIL_DISPATCH[db](season_label)
    if season_data is None:
        abort(404)

    return render_template("year_detail.html", db=db, season=season_data, conferences=TEAM_CONFERENCES)


@app.route("/<db>/year/missing-season")
def missing_season_games(db):
    if db not in VALID_DBS:
        abort(404)
    if db != "mysql":
        abort(404)

    columns, rows = mysql_get_missing_season_games_query()
    return render_template("missing_season_games.html", db=db, columns=columns, rows=rows)


if __name__ == "__main__":
    app.run(debug=True, port=5001)
