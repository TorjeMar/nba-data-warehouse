"""Umbrella frontend for the Basketball Data Warehouse."""

from __future__ import annotations

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template

from src.frontend.backend.constants import VALID_NBA_TRICODES
from src.frontend.backend.routes import register_routes
from src.frontend.backend.season_payloads import format_team_display_name
from src.frontend.backend.stream_cache import StreamStateCache


load_dotenv()

STREAM_CACHE = StreamStateCache()


def get_ksql_team_leaderboard() -> list[dict[str, object]]:
    snapshot = STREAM_CACHE.snapshot()
    rows = snapshot["teams"]

    formatted = []
    for row in rows:
        team_tricode = str(row.get("team_tricode") or "").strip()

        if team_tricode not in VALID_NBA_TRICODES:
            continue

        games_seen = int(row.get("games_seen", 0) or 0)
        total_points = int(row.get("total_points", 0) or 0)

        formatted.append(
            {
                "team_id": int(row["team_id"]),
                "team_tricode": team_tricode,
                "team_name": format_team_display_name(
                    row.get("team_city"),
                    row.get("team_name_raw"),
                ),
                "games_seen": games_seen,
                "total_points": total_points,
                "points_per_game": round(total_points / games_seen, 2) if games_seen else 0.0,
                "total_assists": int(row.get("total_assists", 0) or 0),
                "total_rebounds": int(row.get("total_rebounds", 0) or 0),
                "total_turnovers": int(row.get("total_turnovers", 0) or 0),
            }
        )

    formatted.sort(
        key=lambda r: (
            -r["total_points"],
            -r["points_per_game"],
            r["team_name"],
        )
    )
    return formatted


def get_ksql_player_leaders() -> dict[str, list[dict[str, object]]]:
    snapshot = STREAM_CACHE.snapshot()
    players = [
        row
        for row in snapshot["players"]
        if str(row.get("team_tricode") or "").strip() in VALID_NBA_TRICODES
    ]

    top_scorers = sorted(
        players,
        key=lambda r: (-int(r["total_points"]), str(r.get("display_name") or "")),
    )[:5]

    top_assists = sorted(
        players,
        key=lambda r: (-int(r["total_assists"]), str(r.get("display_name") or "")),
    )[:5]

    top_rebounds = sorted(
        players,
        key=lambda r: (-int(r["total_rebounds"]), str(r.get("display_name") or "")),
    )[:5]

    return {
        "top_scorers": top_scorers,
        "top_assists": top_assists,
        "top_rebounds": top_rebounds,
    }


def get_ksql_dashboard_payload() -> dict[str, object]:
    snapshot = STREAM_CACHE.snapshot()
    team_leaderboard = get_ksql_team_leaderboard()
    leaders = get_ksql_player_leaders()

    return {
        "ready": snapshot["ready"],
        "last_update_ts": snapshot["last_update_ts"],
        "team_leaderboard": team_leaderboard,
        "top_scorers": leaders["top_scorers"],
        "top_assists": leaders["top_assists"],
        "top_rebounds": leaders["top_rebounds"],
    }


def ensure_stream_cache_started() -> None:
    STREAM_CACHE.start()


def create_app() -> Flask:
    flask_app = Flask(__name__)
    register_routes(flask_app)

    @flask_app.route("/stream")
    def stream_dashboard():
        ensure_stream_cache_started()
        return render_template("stream.html")

    @flask_app.route("/api/stream")
    def stream_dashboard_api():
        ensure_stream_cache_started()
        return jsonify(get_ksql_dashboard_payload())

    return flask_app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True, port=5001)
