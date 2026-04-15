// Core indexes for warehouse workloads.

db.player_game_stats.createIndex(
  { sourceGameId: 1, "team.sourceTeamId": 1, "player.sourcePersonId": 1 },
  { unique: true, name: "uq_game_team_player" }
);

db.player_game_stats.createIndex(
  { gameDate: 1 },
  { name: "idx_game_date" }
);

db.player_game_stats.createIndex(
  { "team.sourceTeamId": 1, gameDate: 1 },
  { name: "idx_team_date" }
);

db.player_game_stats.createIndex(
  { "player.sourcePersonId": 1, gameDate: 1 },
  { name: "idx_player_date" }
);

db.player_game_stats.createIndex(
  { seasonLabel: 1, "player.sourcePersonId": 1, "team.sourceTeamId": 1 },
  { name: "idx_season_player_team" }
);

db.player_game_stats.createIndex(
  { gameType: 1, seasonLabel: 1, sourceGameId: 1, "team.sourceTeamId": 1 },
  { name: "idx_game_type_season_team" }
);

db.teams.createIndex(
  { sourceTeamId: 1 },
  { unique: true, name: "uq_team_source_id" }
);

db.players.createIndex(
  { sourcePersonId: 1 },
  { unique: true, name: "uq_player_source_id" }
);

db.games.createIndex(
  { sourceGameId: 1 },
  { unique: true, name: "uq_game_source_id" }
);

db.calendar.createIndex(
  { dateKey: 1 },
  { unique: true, name: "uq_calendar_date_key" }
);
