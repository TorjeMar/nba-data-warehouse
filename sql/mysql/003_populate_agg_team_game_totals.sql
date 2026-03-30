-- Full refresh of team-per-game summary totals.
-- Source: fact_player_game_stats + dim_game
-- Strategy: full rebuild from star-schema tables so corrections/updates in fact data
-- are reflected cleanly on every run.

INSERT INTO agg_team_game_totals (
    game_key,
    date_key,
    team_key,
    total_points,
    total_assists,
    total_rebounds,
    total_steals,
    total_blocks,
    total_turnovers,
    total_field_goals_made,
    total_field_goals_attempted,
    total_three_pointers_made,
    total_three_pointers_attempted,
    total_free_throws_made,
    total_free_throws_attempted,
    total_minutes_seconds
)
SELECT
    f.game_key,
    COALESCE(f.date_key, g.game_date_key) AS date_key,
    f.team_key,
    SUM(f.points) AS total_points,
    SUM(f.assists) AS total_assists,
    SUM(f.rebounds_total) AS total_rebounds,
    SUM(f.steals) AS total_steals,
    SUM(f.blocks) AS total_blocks,
    SUM(f.turnovers) AS total_turnovers,
    SUM(f.field_goals_made) AS total_field_goals_made,
    SUM(f.field_goals_attempted) AS total_field_goals_attempted,
    SUM(f.three_pointers_made) AS total_three_pointers_made,
    SUM(f.three_pointers_attempted) AS total_three_pointers_attempted,
    SUM(f.free_throws_made) AS total_free_throws_made,
    SUM(f.free_throws_attempted) AS total_free_throws_attempted,
    SUM(f.minutes_played_seconds) AS total_minutes_seconds
FROM fact_player_game_stats f
JOIN dim_game g
  ON g.game_key = f.game_key
GROUP BY
    f.game_key,
    COALESCE(f.date_key, g.game_date_key),
    f.team_key;
