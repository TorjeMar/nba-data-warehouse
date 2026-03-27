// Example MongoDB warehouse aggregations.

// Team totals by game.
db.player_game_stats.aggregate([
  {
    $group: {
      _id: {
        sourceGameId: "$sourceGameId",
        sourceTeamId: "$team.sourceTeamId"
      },
      totalPoints: { $sum: "$stats.points" },
      totalAssists: { $sum: "$stats.assists" },
      totalRebounds: { $sum: "$stats.reboundsTotal" },
      totalSteals: { $sum: "$stats.steals" },
      totalBlocks: { $sum: "$stats.blocks" },
      totalTurnovers: { $sum: "$stats.turnovers" },
      totalFieldGoalsMade: { $sum: "$stats.fieldGoalsMade" },
      totalFieldGoalsAttempted: { $sum: "$stats.fieldGoalsAttempted" },
      totalThreePointersMade: { $sum: "$stats.threePointersMade" },
      totalThreePointersAttempted: { $sum: "$stats.threePointersAttempted" },
      totalFreeThrowsMade: { $sum: "$stats.freeThrowsMade" },
      totalFreeThrowsAttempted: { $sum: "$stats.freeThrowsAttempted" },
      totalMinutesPlayedSeconds: { $sum: "$stats.minutesPlayedSeconds" }
    }
  },
  {
    $merge: {
      into: "agg_team_game_totals",
      on: "_id",
      whenMatched: "replace",
      whenNotMatched: "insert"
    }
  }
]);

// Player season totals and averages.
db.player_game_stats.aggregate([
  {
    $group: {
      _id: {
        seasonLabel: "$seasonLabel",
        sourcePersonId: "$player.sourcePersonId",
        sourceTeamId: "$team.sourceTeamId"
      },
      gamesPlayed: { $sum: 1 },
      totalPoints: { $sum: "$stats.points" },
      totalAssists: { $sum: "$stats.assists" },
      totalRebounds: { $sum: "$stats.reboundsTotal" },
      totalSteals: { $sum: "$stats.steals" },
      totalBlocks: { $sum: "$stats.blocks" },
      totalTurnovers: { $sum: "$stats.turnovers" },
      totalMinutesPlayedSeconds: { $sum: "$stats.minutesPlayedSeconds" }
    }
  },
  {
    $addFields: {
      avgPoints: { $divide: ["$totalPoints", "$gamesPlayed"] },
      avgAssists: { $divide: ["$totalAssists", "$gamesPlayed"] },
      avgRebounds: { $divide: ["$totalRebounds", "$gamesPlayed"] }
    }
  },
  {
    $merge: {
      into: "agg_player_season_totals",
      on: "_id",
      whenMatched: "replace",
      whenNotMatched: "insert"
    }
  }
]);
