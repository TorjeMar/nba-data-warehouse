-- Full refresh of player-per-season summary totals.
-- Source: fact_player_game_stats + dim_game
-- Strategy: full rebuild from star-schema tables so corrections/updates in fact data
-- are reflected cleanly on every run.

INSERT INTO agg_player_season_totals (
    season_label,
    player_key,
    team_key,
    games_played,
    total_points,
    total_assists,
    total_rebounds,
    total_steals,
    total_blocks,
    total_turnovers,
    total_minutes_seconds,
    avg_points,
    avg_assists,
    avg_rebounds
)
SELECT
    COALESCE(g.season_label, 'UNKNOWN') AS season_label,
    f.player_key,
    f.team_key,
    COUNT(DISTINCT f.game_key) AS games_played,
    SUM(f.points) AS total_points,
    SUM(f.assists) AS total_assists,
    SUM(f.rebounds_total) AS total_rebounds,
    SUM(f.steals) AS total_steals,
    SUM(f.blocks) AS total_blocks,
    SUM(f.turnovers) AS total_turnovers,
    SUM(f.minutes_played_seconds) AS total_minutes_seconds,
    ROUND(AVG(f.points), 2) AS avg_points,
    ROUND(AVG(f.assists), 2) AS avg_assists,
    ROUND(AVG(f.rebounds_total), 2) AS avg_rebounds
FROM fact_player_game_stats f
JOIN dim_game g
  ON g.game_key = f.game_key
GROUP BY
    COALESCE(g.season_label, 'UNKNOWN'),
    f.player_key,
    f.team_key;
