// Canonical load shape for batched records.
// Expects parameter payload: { rows: [ { ...record params... }, ... ] }

UNWIND $rows AS row

MERGE (team:Team {sourceTeamId: row.sourceTeamId})
SET team.teamName = row.teamName,
    team.teamCity = row.teamCity,
    team.teamTricode = row.teamTricode,
    team.teamSlug = row.teamSlug

MERGE (player:Player {sourcePersonId: row.sourcePersonId})
SET player.firstName = row.firstName,
    player.familyName = row.familyName,
    player.displayName = row.displayName,
    player.nameInitial = row.nameInitial,
    player.playerSlug = row.playerSlug,
    player.jerseyNumber = row.jerseyNumber

MERGE (position:Position {positionCode: coalesce(row.positionCode, "")})
MERGE (player)-[:HAS_POSITION]->(position)

MERGE (game:Game {sourceGameId: row.sourceGameId})
SET game.seasonLabel = row.seasonLabel,
    game.matchupLabel = row.matchupLabel

FOREACH (_ IN CASE WHEN row.gameDate IS NULL THEN [] ELSE [1] END |
  MERGE (date:Date {dateKey: row.dateKey})
  SET date.fullDate = date(row.gameDate),
      date.yearNum = row.yearNum,
      date.monthNum = row.monthNum,
      date.monthName = row.monthName,
      date.quarterNum = row.quarterNum,
      date.dayOfMonth = row.dayOfMonth,
      date.dayOfWeekNum = row.dayOfWeekNum,
      date.dayOfWeekName = row.dayOfWeekName,
      date.isWeekend = row.isWeekend
  MERGE (game)-[:ON_DATE]->(date)
)

MERGE (player)-[:REPRESENTED_TEAM]->(team)

MERGE (player)-[played:PLAYED_IN {sourceGameId: row.sourceGameId, sourceTeamId: row.sourceTeamId}]->(game)
SET played.homeAway = row.homeAway,
    played.minutesPlayedSeconds = row.minutesPlayedSeconds,
    played.fieldGoalsMade = row.fieldGoalsMade,
    played.fieldGoalsAttempted = row.fieldGoalsAttempted,
    played.fieldGoalsPercentage = row.fieldGoalsPercentage,
    played.threePointersMade = row.threePointersMade,
    played.threePointersAttempted = row.threePointersAttempted,
    played.threePointersPercentage = row.threePointersPercentage,
    played.freeThrowsMade = row.freeThrowsMade,
    played.freeThrowsAttempted = row.freeThrowsAttempted,
    played.freeThrowsPercentage = row.freeThrowsPercentage,
    played.reboundsOffensive = row.reboundsOffensive,
    played.reboundsDefensive = row.reboundsDefensive,
    played.reboundsTotal = row.reboundsTotal,
    played.assists = row.assists,
    played.steals = row.steals,
    played.blocks = row.blocks,
    played.turnovers = row.turnovers,
    played.foulsPersonal = row.foulsPersonal,
    played.points = row.points,
    played.plusMinusPoints = row.plusMinusPoints,
    played.playerStatusComment = row.playerStatusComment,
    played.updatedAt = datetime()
