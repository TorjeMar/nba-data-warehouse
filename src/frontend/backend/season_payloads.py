"""Shared helpers for season and playoff payload rendering."""

from __future__ import annotations

from src.frontend.backend.constants import PLAYOFF_ROUND_NAMES, TEAM_CONFERENCES


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


def _parse_round_num_from_source_game_id(source_game_id: str) -> int | None:
    if len(source_game_id) <= 7:
        return None
    digit = source_game_id[7]
    if not digit.isdigit():
        return None
    round_num = int(digit)
    return round_num if 1 <= round_num <= 4 else None


def _series_sort_key(series: dict[str, object]) -> tuple[object, ...]:
    game_date_key = series.get("latest_game_date_key")
    return (
        game_date_key is None,
        game_date_key if game_date_key is not None else 0,
        str(series["series_key"]),
    )


def _series_winner_team_id(series: dict[str, object]) -> int | None:
    team_items = list(series["teams"].items())
    if len(team_items) != 2:
        return None

    winner_id, winner_team = max(
        team_items,
        key=lambda item: (int(item[1]["wins"]), -int(item[0])),
    )
    loser_id, loser_team = min(
        team_items,
        key=lambda item: (int(item[1]["wins"]), -int(item[0])),
    )

    if int(winner_team["wins"]) == int(loser_team["wins"]):
        return None
    return int(winner_id)


def _series_participant_team_ids(series: dict[str, object]) -> set[int]:
    return {int(team_id) for team_id in series["teams"].keys()}


def _infer_legacy_rounds(series_map: dict[str, dict[str, object]]) -> None:
    finals_series = []
    conference_champions: dict[str, int] = {}

    for series in series_map.values():
        team_ids = list(series["teams"].keys())
        if len(team_ids) != 2:
            continue

        team_one_conf = TEAM_CONFERENCES.get(str(series["teams"][team_ids[0]]["tricode"]))
        team_two_conf = TEAM_CONFERENCES.get(str(series["teams"][team_ids[1]]["tricode"]))
        if team_one_conf and team_two_conf and team_one_conf != team_two_conf:
            series["round_num"] = 4
            finals_series.append(series)
            for team_id in team_ids:
                team_conf = TEAM_CONFERENCES.get(str(series["teams"][team_id]["tricode"]))
                if team_conf is not None:
                    conference_champions[team_conf] = int(team_id)

    for conference in ("East", "West"):
        conference_series = [
            series
            for series in series_map.values()
            if series.get("round_num") is None
            and len(series["teams"]) == 2
            and all(
                TEAM_CONFERENCES.get(str(team["tricode"])) == conference
                for team in series["teams"].values()
            )
        ]
        if not conference_series:
            continue

        champion_team_id = conference_champions.get(conference)
        conference_final: dict[str, object] | None = None
        if champion_team_id is not None:
            candidate_finals = [
                series
                for series in conference_series
                if champion_team_id in _series_participant_team_ids(series)
            ]
            if candidate_finals:
                conference_final = max(candidate_finals, key=_series_sort_key)
                conference_final["round_num"] = 3

        if conference_final is not None:
            conference_final_participants = _series_participant_team_ids(conference_final)
            for finalist_team_id in conference_final_participants:
                finalist_path = [
                    series
                    for series in conference_series
                    if series.get("round_num") is None
                    and finalist_team_id in _series_participant_team_ids(series)
                    and _series_winner_team_id(series) == finalist_team_id
                ]
                if finalist_path:
                    semifinal = max(finalist_path, key=_series_sort_key)
                    semifinal["round_num"] = 2

        for series in conference_series:
            if series.get("round_num") is None:
                series["round_num"] = 1

    for series in series_map.values():
        if series.get("round_num") is None:
            series["round_num"] = 1


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

        parsed_round_num = _parse_round_num_from_source_game_id(source_game_id)
        first, second = game_rows
        pair_key = "-".join(str(team_id) for team_id in sorted((int(first["team_id"]), int(second["team_id"]))))
        series_key = source_game_id[:9] if parsed_round_num is not None else pair_key
        series = series_map.setdefault(
            series_key,
            {
                "round_num": parsed_round_num,
                "series_key": series_key,
                "latest_game_date_key": None,
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
        game_date_key = first.get("game_date_key") or second.get("game_date_key")
        if game_date_key is not None:
            current_latest = series.get("latest_game_date_key")
            if current_latest is None or game_date_key > current_latest:
                series["latest_game_date_key"] = game_date_key

    if any(series.get("round_num") is None for series in series_map.values()):
        _infer_legacy_rounds(series_map)

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

    for series in sorted(
        series_map.values(),
        key=lambda item: (int(item.get("round_num") or 1), _series_sort_key(item)),
    ):
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
        if round_num < 1 or round_num > 3:
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
        "playoff_bracket": playoff_bracket if playoff_series_rows else None,
    }
