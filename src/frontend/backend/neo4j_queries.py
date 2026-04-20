"""Neo4j query functions for the frontend."""

from __future__ import annotations

from src.clients.neo4j_client import connect_neo4j
from src.frontend.backend.season_payloads import build_season_payload, format_team_display_name


REGULAR_SEASON_WHERE = "g.gameType = 'regular_season'"

PLAYOFF_WHERE = "g.gameType = 'playoffs'"


def neo4j_team_query():
    driver = connect_neo4j()
    with driver.session() as session:
        # Team basics
        result = session.run(
            f"""
            MATCH (g:Game)<-[played:PLAYED_IN]-(:Player)
            MATCH (team:Team {{sourceTeamId: played.sourceTeamId}})
            WHERE {REGULAR_SEASON_WHERE}
            WITH team, sum(played.points) AS pts, sum(played.assists) AS ast
            RETURN team.sourceTeamId AS id,
                   team.teamTricode AS tricode,
                   team.teamCity AS city,
                   team.teamName AS name,
                   pts, ast
            ORDER BY team.teamName ASC
            """
        )
        team_data = [record.data() for record in result]

        team_ids = [int(t["id"]) for t in team_data]
        if not team_ids:
            driver.close()
            return [], []

        # Top scorer per team
        scorer_result = session.run(
            f"""
            MATCH (g:Game)<-[played:PLAYED_IN]-(player:Player)
            MATCH (team:Team {{sourceTeamId: played.sourceTeamId}})
            WHERE {REGULAR_SEASON_WHERE}
            WITH team.sourceTeamId AS team_id, player.displayName AS name, sum(played.points) AS pts
            ORDER BY team_id, pts DESC, name ASC
            WITH team_id, collect(name)[0] AS top_name
            RETURN team_id, top_name
            """
        )
        scorer_map = {int(r["team_id"]): r["top_name"] for r in scorer_result}

        # Top assist per team
        assist_result = session.run(
            f"""
            MATCH (g:Game)<-[played:PLAYED_IN]-(player:Player)
            MATCH (team:Team {{sourceTeamId: played.sourceTeamId}})
            WHERE {REGULAR_SEASON_WHERE}
            WITH team.sourceTeamId AS team_id, player.displayName AS name, sum(played.assists) AS ast
            ORDER BY team_id, ast DESC, name ASC
            WITH team_id, collect(name)[0] AS top_name
            RETURN team_id, top_name
            """
        )
        assist_map = {int(r["team_id"]): r["top_name"] for r in assist_result}

        # Championship count per team
        title_result = session.run(
            """
            MATCH (g:Game)<-[played:PLAYED_IN]-(:Player)
            WHERE g.gameType = 'playoffs'
              AND substring(g.sourceGameId, 7, 1) = '4'
            WITH g.seasonLabel AS season_label, g.sourceGameId AS source_game_id,
                 played.sourceTeamId AS team_id, sum(played.points) AS team_points
            WITH season_label, source_game_id, team_id, team_points
            ORDER BY source_game_id, team_points DESC
            WITH season_label, source_game_id, collect(team_id)[0] AS winner_id
            WITH season_label, winner_id, count(*) AS wins
            WHERE wins >= 4
            RETURN winner_id AS team_id, count(*) AS titles
            """
        )
        titles_map = {int(r["team_id"]): int(r["titles"]) for r in title_result}

    driver.close()

    rows = []
    for t in team_data:
        team_id = int(t["id"])
        rows.append({
            "id": team_id,
            "tricode": t["tricode"],
            "name": format_team_display_name(t["city"], t["name"]),
            "top_scorer": scorer_map.get(team_id, "No data"),
            "top_assist": assist_map.get(team_id, "No data"),
            "titles": titles_map.get(team_id, 0),
        })

    columns = ["id", "tricode", "name", "top_scorer", "top_assist", "titles"]
    return columns, rows


def neo4j_get_team_detail_query(team_id) -> dict[str, object] | None:
    driver = connect_neo4j()
    team_id = int(team_id)
    with driver.session() as session:
        summary_result = session.run(
            """
            MATCH (team:Team {sourceTeamId: $team_id})
            OPTIONAL MATCH (g:Game)<-[played:PLAYED_IN {sourceTeamId: team.sourceTeamId}]-(:Player)
            RETURN team.teamTricode AS tricode,
                   team.teamCity AS city,
                   team.teamName AS name,
                   count(DISTINCT g.sourceGameId) AS games_count,
                   count(DISTINCT played.sourcePersonId) AS players_count,
                   coalesce(sum(played.points), 0) AS total_points,
                   coalesce(sum(played.assists), 0) AS total_assists,
                   coalesce(sum(played.reboundsTotal), 0) AS total_rebounds
            """,
            team_id=team_id,
        )
        summary = summary_result.single()
        if summary is None or summary["tricode"] is None:
            driver.close()
            return None

        summary = summary.data()
        games_count = int(summary["games_count"]) or 1

        player_result = session.run(
            """
            MATCH (team:Team {sourceTeamId: $team_id})
            MATCH (g:Game)<-[played:PLAYED_IN {sourceTeamId: team.sourceTeamId}]-(player:Player)
            RETURN player.displayName AS player_name,
                   count(DISTINCT g.sourceGameId) AS games,
                   sum(played.points) AS total_points,
                   sum(played.assists) AS total_assists,
                   sum(played.reboundsTotal) AS total_rebounds
            ORDER BY total_points DESC, player_name ASC
            LIMIT 10
            """,
            team_id=team_id,
        )
        top_players = []
        for record in player_result:
            row = record.data()
            pg = int(row["games"]) or 1
            top_players.append({
                "player_name": row["player_name"],
                "games": row["games"],
                "total_points": row["total_points"],
                "ppg": round(int(row["total_points"]) / pg, 1),
                "total_assists": row["total_assists"],
                "apg": round(int(row["total_assists"]) / pg, 1),
                "total_rebounds": row["total_rebounds"],
                "rpg": round(int(row["total_rebounds"]) / pg, 1),
            })

        season_result = session.run(
            """
            MATCH (team:Team {sourceTeamId: $team_id})
            MATCH (g:Game)<-[played:PLAYED_IN {sourceTeamId: team.sourceTeamId}]-(:Player)
            WHERE g.seasonLabel IS NOT NULL AND trim(g.seasonLabel) <> ''
            WITH g.seasonLabel AS season_label,
                 collect(DISTINCT g.sourceGameId) AS games,
                 sum(played.points) AS total_points
            RETURN season_label, size(games) AS games, total_points
            ORDER BY season_label DESC
            """,
            team_id=team_id,
        )
        seasons = []
        for record in season_result:
            row = record.data()
            sg = int(row["games"]) or 1
            seasons.append({
                "season_label": row["season_label"],
                "games": row["games"],
                "total_points": row["total_points"],
                "ppg": round(int(row["total_points"]) / sg, 1),
            })

        title_result = session.run(
            """
            MATCH (team:Team {sourceTeamId: $team_id})
            MATCH (g:Game)<-[played:PLAYED_IN {sourceTeamId: team.sourceTeamId}]-(:Player)
            WHERE g.gameType = 'playoffs'
              AND substring(g.sourceGameId, 7, 1) = '4'
            WITH g.seasonLabel AS season_label, g.sourceGameId AS source_game_id,
                 sum(played.points) AS team_points
            WITH season_label, source_game_id, team_points
            MATCH (g2:Game {sourceGameId: source_game_id})<-[opp:PLAYED_IN]-(:Player)
            WHERE opp.sourceTeamId <> $team_id
            WITH season_label, source_game_id, team_points, sum(opp.points) AS opp_points
            WHERE team_points > opp_points
            WITH season_label, count(*) AS wins
            WHERE wins >= 4
            RETURN season_label
            ORDER BY season_label DESC
            """,
            team_id=team_id,
        )
        title_seasons = [record["season_label"] for record in title_result]

    driver.close()
    return {
        "id": team_id,
        "tricode": summary["tricode"],
        "city": summary.get("city", ""),
        "name": summary.get("name", ""),
        "full_name": format_team_display_name(summary.get("city"), summary.get("name")),
        "games_count": summary["games_count"],
        "players_count": summary["players_count"],
        "total_points": summary["total_points"],
        "total_assists": summary["total_assists"],
        "total_rebounds": summary["total_rebounds"],
        "ppg": round(int(summary["total_points"]) / games_count, 1),
        "apg": round(int(summary["total_assists"]) / games_count, 1),
        "rpg": round(int(summary["total_rebounds"]) / games_count, 1),
        "titles": len(title_seasons),
        "title_seasons": title_seasons,
        "top_players": top_players,
        "seasons": seasons,
    }


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
