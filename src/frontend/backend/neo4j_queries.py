"""Neo4j query functions for the frontend."""

from __future__ import annotations

from src.clients.neo4j_client import connect_neo4j
from src.frontend.backend.season_payloads import build_season_payload


REGULAR_SEASON_WHERE = "g.gameType = 'regular_season'"

PLAYOFF_WHERE = "g.gameType = 'playoffs'"


def neo4j_team_query():
    driver = connect_neo4j()

    # TODO: write your Neo4j team Cypher query here
    columns, rows = [], []

    driver.close()
    return columns, rows


def neo4j_year_query():
    driver = connect_neo4j()
    with driver.session() as session:
        result = session.run(
            f"""
            MATCH (g:Game)<-[played:PLAYED_IN]-(:Player)
            MATCH (team:Team {{sourceTeamId: played.sourceTeamId}})
            WHERE {REGULAR_SEASON_WHERE}
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


def neo4j_get_season_detail_query(season_label: str) -> dict[str, object] | None:
    driver = connect_neo4j()
    with driver.session() as session:
        team_game_rows = [
            record.data()
            for record in session.run(
                f"""
                MATCH (g:Game)<-[played:PLAYED_IN]-(:Player)
                MATCH (team:Team {{sourceTeamId: played.sourceTeamId}})
                WHERE {REGULAR_SEASON_WHERE}
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
                f"""
                MATCH (g:Game)<-[played:PLAYED_IN]-(player:Player)
                MATCH (team:Team {{sourceTeamId: played.sourceTeamId}})
                WHERE {REGULAR_SEASON_WHERE}
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
                f"""
                MATCH (g:Game)<-[played:PLAYED_IN]-(:Player)
                MATCH (team:Team {{sourceTeamId: played.sourceTeamId}})
                WHERE {PLAYOFF_WHERE}
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
