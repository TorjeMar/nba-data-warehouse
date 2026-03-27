// Basketball warehouse graph model.
// Grain: one PLAYED_IN relationship per player, game, and team.
//
// Node labels:
// - Player
// - Team
// - Game
// - Date
// - Position
//
// Relationship patterns:
// (Player)-[:HAS_POSITION]->(Position)
// (Game)-[:ON_DATE]->(Date)
// (Game)-[:HOME_TEAM]->(Team)
// (Game)-[:AWAY_TEAM]->(Team)
// (Player)-[r:PLAYED_IN]->(Game)
// (Player)-[r:REPRESENTED_TEAM]->(Team)
//
// Recommended fact-like shape:
// Keep the player box score metrics on the PLAYED_IN relationship because the
// measures describe the player's participation in a specific game.

MERGE (posUnknown:Position {positionCode: ""})
SET posUnknown.positionGroup = "Unknown";

MERGE (posGuard:Position {positionCode: "G"})
SET posGuard.positionGroup = "Backcourt";

MERGE (posForward:Position {positionCode: "F"})
SET posForward.positionGroup = "Frontcourt";

MERGE (posCenter:Position {positionCode: "C"})
SET posCenter.positionGroup = "Frontcourt";

MERGE (posGF:Position {positionCode: "G-F"})
SET posGF.positionGroup = "Hybrid";

MERGE (posFC:Position {positionCode: "F-C"})
SET posFC.positionGroup = "Hybrid";
