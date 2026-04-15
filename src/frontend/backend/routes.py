"""Flask route registration for the frontend app."""

from __future__ import annotations

from flask import abort, render_template

from src.frontend.backend.constants import TEAM_CONFERENCES, VALID_DBS


def get_query_dispatch():
    from src.frontend.backend.mongodb_queries import mongodb_team_query, mongodb_year_query
    from src.frontend.backend.mysql_queries import mysql_get_teams_query, mysql_year_query
    from src.frontend.backend.neo4j_queries import neo4j_team_query, neo4j_year_query

    return {
        ("mysql", "team"): mysql_get_teams_query,
        ("mysql", "year"): mysql_year_query,
        ("mongodb", "team"): mongodb_team_query,
        ("mongodb", "year"): mongodb_year_query,
        ("neo4j", "team"): neo4j_team_query,
        ("neo4j", "year"): neo4j_year_query,
    }


def get_year_detail_dispatch():
    from src.frontend.backend.mongodb_queries import mongodb_get_season_detail_query
    from src.frontend.backend.mysql_queries import mysql_get_season_detail_query
    from src.frontend.backend.neo4j_queries import neo4j_get_season_detail_query

    return {
        "mysql": mysql_get_season_detail_query,
        "mongodb": mongodb_get_season_detail_query,
        "neo4j": neo4j_get_season_detail_query,
    }


def get_team_detail_dispatch():
    from src.frontend.backend.mongodb_queries import mongodb_get_team_detail_query
    from src.frontend.backend.mysql_queries import mysql_get_team_detail_query
    from src.frontend.backend.neo4j_queries import neo4j_get_team_detail_query

    return {
        "mysql": mysql_get_team_detail_query,
        "mongodb": mongodb_get_team_detail_query,
        "neo4j": neo4j_get_team_detail_query,
    }


def register_routes(app) -> None:
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
        query_fn = get_query_dispatch()[(db, "team")]

        columns, rows = query_fn()
        if db == "mysql":
            from src.frontend.backend.mysql_queries import mysql_get_other_teams_count

            other_teams_count = mysql_get_other_teams_count()
        else:
            other_teams_count = 0
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

        from src.frontend.backend.mysql_queries import mysql_get_other_teams_query

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

        team_data = get_team_detail_dispatch()[db](team_id)
        if team_data is None:
            abort(404)

        return render_template("team_detail.html", db=db, team=team_data)

    @app.route("/<db>/year")
    def year(db):
        if db not in VALID_DBS:
            abort(404)
        query_fn = get_query_dispatch()[(db, "year")]
        columns, rows = query_fn()
        if db == "mysql":
            from src.frontend.backend.mysql_queries import mysql_get_missing_season_games_count

            missing_season_games_count = mysql_get_missing_season_games_count()
        else:
            missing_season_games_count = 0
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

        season_data = get_year_detail_dispatch()[db](season_label)
        if season_data is None:
            abort(404)

        return render_template("year_detail.html", db=db, season=season_data, conferences=TEAM_CONFERENCES)

    @app.route("/<db>/year/missing-season")
    def missing_season_games(db):
        if db not in VALID_DBS:
            abort(404)
        if db != "mysql":
            abort(404)

        from src.frontend.backend.mysql_queries import mysql_get_missing_season_games_query

        columns, rows = mysql_get_missing_season_games_query()
        return render_template("missing_season_games.html", db=db, columns=columns, rows=rows)
