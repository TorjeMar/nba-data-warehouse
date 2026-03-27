// Canonical load shape for one source record.
// Replace parameter names with ETL-provided values during ingestion.

MERGE (team:Team {sourceTeamId: $sourceTeamId})
SET team.teamName = $teamName,
    team.teamCity = $teamCity,
    team.teamTricode = $teamTricode,
    team.teamSlug = $teamSlug;

MERGE (player:Player {sourcePersonId: $sourcePersonId})
SET player.firstName = $firstName,
    player.familyName = $familyName,
    player.displayName = $displayName,
    player.nameInitial = $nameInitial,
    player.playerSlug = $playerSlug,
    player.jerseyNumber = $jerseyNumber;

MERGE (position:Position {positionCode: coalesce($positionCode, "")});
MERGE (player)-[:HAS_POSITION]->(position);

MERGE (game:Game {sourceGameId: $sourceGameId})
SET game.seasonLabel = $seasonLabel,
    game.matchupLabel = $matchupLabel;

FOREACH (_ IN CASE WHEN $gameDate IS NULL THEN [] ELSE [1] END |
  MERGE (date:Date {dateKey: $dateKey})
  SET date.fullDate = date($gameDate),
      date.yearNum = $yearNum,
      date.monthNum = $monthNum,
      date.monthName = $monthName,
      date.quarterNum = $quarterNum,
      date.dayOfMonth = $dayOfMonth,
      date.dayOfWeekNum = $dayOfWeekNum,
      date.dayOfWeekName = $dayOfWeekName,
      date.isWeekend = $isWeekend
  MERGE (game)-[:ON_DATE]->(date)
);

MERGE (player)-[:REPRESENTED_TEAM]->(team);

MERGE (player)-[played:PLAYED_IN {sourceGameId: $sourceGameId, sourceTeamId: $sourceTeamId}]->(game)
SET played.minutesPlayedSeconds = $minutesPlayedSeconds,
    played.fieldGoalsMade = $fieldGoalsMade,
    played.fieldGoalsAttempted = $fieldGoalsAttempted,
    played.fieldGoalsPercentage = $fieldGoalsPercentage,
    played.threePointersMade = $threePointersMade,
    played.threePointersAttempted = $threePointersAttempted,
    played.threePointersPercentage = $threePointersPercentage,
    played.freeThrowsMade = $freeThrowsMade,
    played.freeThrowsAttempted = $freeThrowsAttempted,
    played.freeThrowsPercentage = $freeThrowsPercentage,
    played.reboundsOffensive = $reboundsOffensive,
    played.reboundsDefensive = $reboundsDefensive,
    played.reboundsTotal = $reboundsTotal,
    played.assists = $assists,
    played.steals = $steals,
    played.blocks = $blocks,
    played.turnovers = $turnovers,
    played.foulsPersonal = $foulsPersonal,
    played.points = $points,
    played.plusMinusPoints = $plusMinusPoints,
    played.playerStatusComment = $playerStatusComment,
    played.updatedAt = datetime();
