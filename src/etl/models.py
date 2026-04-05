"""Shared ETL data models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class WarehouseRecord:
    """Canonical warehouse record with one player-game-team grain."""

    source_game_id: str
    source_team_id: int
    team_city: str
    team_name: str
    team_tricode: str
    team_slug: str
    source_person_id: int
    first_name: str
    family_name: str
    display_name: str
    name_initial: str | None
    player_slug: str | None
    position_code: str | None
    player_status_comment: str | None
    jersey_number: str | None
    minutes_raw: str | None
    minutes_played_seconds: int
    field_goals_made: int
    field_goals_attempted: int
    field_goals_percentage: float | None
    three_pointers_made: int
    three_pointers_attempted: int
    three_pointers_percentage: float | None
    free_throws_made: int
    free_throws_attempted: int
    free_throws_percentage: float | None
    rebounds_offensive: int
    rebounds_defensive: int
    rebounds_total: int
    assists: int
    steals: int
    blocks: int
    turnovers: int
    fouls_personal: int
    points: int
    plus_minus_points: float
    season_label: str | None = None
    game_date: datetime | None = None
    matchup_label: str | None = None
    home_away: str | None = None
    source_row_hash: str | None = None

    def mysql_fact_params(self) -> dict[str, Any]:
        return {
            "source_game_id": self.source_game_id,
            "source_team_id": self.source_team_id,
            "source_person_id": self.source_person_id,
            "position_code": self.position_code or "",
            "minutes_played_seconds": self.minutes_played_seconds,
            "field_goals_made": self.field_goals_made,
            "field_goals_attempted": self.field_goals_attempted,
            "field_goals_percentage": self.field_goals_percentage,
            "three_pointers_made": self.three_pointers_made,
            "three_pointers_attempted": self.three_pointers_attempted,
            "three_pointers_percentage": self.three_pointers_percentage,
            "free_throws_made": self.free_throws_made,
            "free_throws_attempted": self.free_throws_attempted,
            "free_throws_percentage": self.free_throws_percentage,
            "rebounds_offensive": self.rebounds_offensive,
            "rebounds_defensive": self.rebounds_defensive,
            "rebounds_total": self.rebounds_total,
            "assists": self.assists,
            "steals": self.steals,
            "blocks": self.blocks,
            "turnovers": self.turnovers,
            "fouls_personal": self.fouls_personal,
            "points": self.points,
            "plus_minus_points": int(round(self.plus_minus_points)),
            "player_status_comment": self.player_status_comment,
            "source_row_hash": self.source_row_hash,
        }

    def mongodb_document(self) -> dict[str, Any]:
        return {
            "sourceGameId": self.source_game_id,
            "seasonLabel": self.season_label,
            "gameDate": self.game_date.strftime("%Y-%m-%d") if self.game_date else None,
            "team": {
                "sourceTeamId": self.source_team_id,
                "teamCity": self.team_city,
                "teamName": self.team_name,
                "teamTricode": self.team_tricode,
                "teamSlug": self.team_slug,
            },
            "player": {
                "sourcePersonId": self.source_person_id,
                "firstName": self.first_name,
                "familyName": self.family_name,
                "displayName": self.display_name,
                "nameInitial": self.name_initial,
                "playerSlug": self.player_slug,
                "position": self.position_code,
                "jerseyNumber": self.jersey_number,
            },
            "matchupLabel": self.matchup_label,
            "homeAway": self.home_away,
            "stats": {
                "minutesPlayedSeconds": self.minutes_played_seconds,
                "fieldGoalsMade": self.field_goals_made,
                "fieldGoalsAttempted": self.field_goals_attempted,
                "fieldGoalsPercentage": self.field_goals_percentage,
                "threePointersMade": self.three_pointers_made,
                "threePointersAttempted": self.three_pointers_attempted,
                "threePointersPercentage": self.three_pointers_percentage,
                "freeThrowsMade": self.free_throws_made,
                "freeThrowsAttempted": self.free_throws_attempted,
                "freeThrowsPercentage": self.free_throws_percentage,
                "reboundsOffensive": self.rebounds_offensive,
                "reboundsDefensive": self.rebounds_defensive,
                "reboundsTotal": self.rebounds_total,
                "assists": self.assists,
                "steals": self.steals,
                "blocks": self.blocks,
                "turnovers": self.turnovers,
                "foulsPersonal": self.fouls_personal,
                "points": self.points,
                "plusMinusPoints": self.plus_minus_points,
            },
            "playerStatusComment": self.player_status_comment,
            "sourceRowHash": self.source_row_hash,
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow(),
        }

    def neo4j_params(self) -> dict[str, Any]:
        game_date = self.game_date
        date_key = int(game_date.strftime("%Y%m%d")) if game_date else None
        return {
            "sourceGameId": self.source_game_id,
            "sourceTeamId": self.source_team_id,
            "teamCity": self.team_city,
            "teamName": self.team_name,
            "teamTricode": self.team_tricode,
            "teamSlug": self.team_slug,
            "sourcePersonId": self.source_person_id,
            "firstName": self.first_name,
            "familyName": self.family_name,
            "displayName": self.display_name,
            "nameInitial": self.name_initial,
            "playerSlug": self.player_slug,
            "positionCode": self.position_code or "",
            "playerStatusComment": self.player_status_comment,
            "jerseyNumber": self.jersey_number,
            "seasonLabel": self.season_label,
            "matchupLabel": self.matchup_label,
            "homeAway": self.home_away,
            "gameDate": game_date,
            "dateKey": date_key,
            "yearNum": self.game_date.year if self.game_date else None,
            "monthNum": self.game_date.month if self.game_date else None,
            "monthName": self.game_date.strftime("%B") if self.game_date else None,
            "quarterNum": ((self.game_date.month - 1) // 3) + 1 if self.game_date else None,
            "dayOfMonth": self.game_date.day if self.game_date else None,
            "dayOfWeekNum": self.game_date.isoweekday() if self.game_date else None,
            "dayOfWeekName": self.game_date.strftime("%A") if self.game_date else None,
            "isWeekend": self.game_date.isoweekday() >= 6 if self.game_date else None,
            "minutesPlayedSeconds": self.minutes_played_seconds,
            "fieldGoalsMade": self.field_goals_made,
            "fieldGoalsAttempted": self.field_goals_attempted,
            "fieldGoalsPercentage": self.field_goals_percentage,
            "threePointersMade": self.three_pointers_made,
            "threePointersAttempted": self.three_pointers_attempted,
            "threePointersPercentage": self.three_pointers_percentage,
            "freeThrowsMade": self.free_throws_made,
            "freeThrowsAttempted": self.free_throws_attempted,
            "freeThrowsPercentage": self.free_throws_percentage,
            "reboundsOffensive": self.rebounds_offensive,
            "reboundsDefensive": self.rebounds_defensive,
            "reboundsTotal": self.rebounds_total,
            "assists": self.assists,
            "steals": self.steals,
            "blocks": self.blocks,
            "turnovers": self.turnovers,
            "foulsPersonal": self.fouls_personal,
            "points": self.points,
            "plusMinusPoints": self.plus_minus_points,
        }
