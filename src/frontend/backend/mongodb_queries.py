"""MongoDB query functions for the frontend."""

from __future__ import annotations

from src.clients.mongodb_client import connect_mongodb
from src.frontend.backend.season_payloads import build_season_payload, format_team_display_name


def mongodb_team_query():
    db = connect_mongodb()

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
    db = connect_mongodb()
    pipeline = [
        {
            "$match": {
                "gameType": "regular_season",
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


def mongodb_get_season_detail_query(season_label: str) -> dict[str, object] | None:
    db = connect_mongodb()

    regular_team_game_pipeline = [
        {"$match": {"gameType": "regular_season", "seasonLabel": season_label}},
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
        {"$match": {"gameType": "regular_season", "seasonLabel": season_label}},
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
        {"$match": {"gameType": "playoffs", "seasonLabel": season_label}},
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
