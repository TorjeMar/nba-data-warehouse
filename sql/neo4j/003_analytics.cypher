// Example warehouse analytics in Neo4j.

// Team totals by game.
MATCH (p:Player)-[s:PLAYED_IN]->(g:Game)
MATCH (p)-[:REPRESENTED_TEAM]->(t:Team)
RETURN
  g.sourceGameId AS sourceGameId,
  t.sourceTeamId AS sourceTeamId,
  t.teamName AS teamName,
  sum(s.points) AS totalPoints,
  sum(s.assists) AS totalAssists,
  sum(s.reboundsTotal) AS totalRebounds,
  sum(s.steals) AS totalSteals,
  sum(s.blocks) AS totalBlocks,
  sum(s.turnovers) AS totalTurnovers
ORDER BY sourceGameId, sourceTeamId;

// Player season totals and averages.
MATCH (p:Player)-[s:PLAYED_IN]->(g:Game)
MATCH (p)-[:REPRESENTED_TEAM]->(t:Team)
WHERE g.seasonLabel IS NOT NULL
RETURN
  g.seasonLabel AS seasonLabel,
  p.sourcePersonId AS sourcePersonId,
  p.displayName AS playerName,
  t.sourceTeamId AS sourceTeamId,
  t.teamName AS teamName,
  count(s) AS gamesPlayed,
  sum(s.points) AS totalPoints,
  sum(s.assists) AS totalAssists,
  sum(s.reboundsTotal) AS totalRebounds,
  round(toFloat(sum(s.points)) / count(s), 2) AS avgPoints,
  round(toFloat(sum(s.assists)) / count(s), 2) AS avgAssists,
  round(toFloat(sum(s.reboundsTotal)) / count(s), 2) AS avgRebounds
ORDER BY seasonLabel, totalPoints DESC;

// Top scoring players for a team.
MATCH (p:Player)-[s:PLAYED_IN]->(:Game)
MATCH (p)-[:REPRESENTED_TEAM]->(t:Team {sourceTeamId: $sourceTeamId})
RETURN
  p.sourcePersonId AS sourcePersonId,
  p.displayName AS playerName,
  count(s) AS gamesPlayed,
  sum(s.points) AS totalPoints,
  round(toFloat(sum(s.points)) / count(s), 2) AS avgPoints
ORDER BY totalPoints DESC
LIMIT 10;
