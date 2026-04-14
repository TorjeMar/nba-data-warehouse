CREATE STREAM IF NOT EXISTS PLAYER_GAME_EVENTS_RAW (
  event_id VARCHAR,
  event_type VARCHAR,
  schema_version VARCHAR,
  partition_key VARCHAR,
  ingested_at_utc VARCHAR,
  trace STRUCT<
    producer_name VARCHAR,
    producer_run_id VARCHAR,
    source_file VARCHAR,
    source_line INTEGER
  >,
  payload STRUCT<
    source_game_id VARCHAR,
    source_team_id INTEGER,
    team_city VARCHAR,
    team_name VARCHAR,
    team_tricode VARCHAR,
    team_slug VARCHAR,
    source_person_id INTEGER,
    first_name VARCHAR,
    family_name VARCHAR,
    display_name VARCHAR,
    name_initial VARCHAR,
    player_slug VARCHAR,
    position_code VARCHAR,
    player_status_comment VARCHAR,
    jersey_number VARCHAR,
    minutes_raw VARCHAR,
    minutes_played_seconds INTEGER,
    field_goals_made INTEGER,
    field_goals_attempted INTEGER,
    field_goals_percentage DOUBLE,
    three_pointers_made INTEGER,
    three_pointers_attempted INTEGER,
    three_pointers_percentage DOUBLE,
    free_throws_made INTEGER,
    free_throws_attempted INTEGER,
    free_throws_percentage DOUBLE,
    rebounds_offensive INTEGER,
    rebounds_defensive INTEGER,
    rebounds_total INTEGER,
    assists INTEGER,
    steals INTEGER,
    blocks INTEGER,
    turnovers INTEGER,
    fouls_personal INTEGER,
    points INTEGER,
    plus_minus_points DOUBLE,
    season_label VARCHAR,
    game_date VARCHAR,
    matchup_label VARCHAR,
    home_away VARCHAR,
    source_row_hash VARCHAR
  >
) WITH (
  KAFKA_TOPIC = 'player-game-records',
  PARTITIONS = 1,
  REPLICAS = 1,
  VALUE_FORMAT = 'JSON'
);

CREATE STREAM PLAYER_GAME_EVENTS_FLAT AS
SELECT
  payload->source_game_id   AS source_game_id,
  payload->source_team_id   AS source_team_id,
  payload->team_city        AS team_city,
  payload->team_name        AS team_name,
  payload->team_tricode     AS team_tricode,
  payload->source_person_id AS source_person_id,
  payload->display_name     AS display_name,
  payload->season_label     AS season_label,
  payload->points           AS points,
  payload->assists          AS assists,
  payload->rebounds_total   AS rebounds_total,
  payload->turnovers        AS turnovers,
  CONCAT(payload->source_game_id, ':', CAST(payload->source_team_id AS STRING)) AS game_team_key,
  CAST(payload->source_team_id AS STRING) AS team_key,
  CAST(payload->source_person_id AS STRING) AS player_key
FROM PLAYER_GAME_EVENTS_RAW
EMIT CHANGES;

CREATE TABLE TEAM_GAME_TOTALS AS
SELECT
  game_team_key,
  LATEST_BY_OFFSET(source_game_id) AS source_game_id,
  LATEST_BY_OFFSET(source_team_id) AS source_team_id,
  LATEST_BY_OFFSET(team_tricode)   AS team_tricode,
  LATEST_BY_OFFSET(team_city)      AS team_city,
  LATEST_BY_OFFSET(team_name)      AS team_name,
  COUNT(*)                         AS player_rows_seen,
  SUM(points)                      AS team_points,
  SUM(assists)                     AS team_assists,
  SUM(rebounds_total)              AS team_rebounds,
  SUM(turnovers)                   AS team_turnovers
FROM PLAYER_GAME_EVENTS_FLAT
GROUP BY game_team_key
EMIT CHANGES;

CREATE TABLE PLAYER_STREAM_TOTALS AS
SELECT
  player_key,
  LATEST_BY_OFFSET(source_person_id) AS source_person_id,
  LATEST_BY_OFFSET(display_name)     AS display_name,
  LATEST_BY_OFFSET(team_tricode)     AS team_tricode,
  COUNT(*)                           AS player_rows_seen,
  SUM(points)                        AS total_points,
  SUM(assists)                       AS total_assists,
  SUM(rebounds_total)                AS total_rebounds
FROM PLAYER_GAME_EVENTS_FLAT
GROUP BY player_key
EMIT CHANGES;

CREATE TABLE TEAM_STREAM_TOTALS AS
SELECT
  team_key,
  LATEST_BY_OFFSET(source_team_id) AS source_team_id,
  LATEST_BY_OFFSET(team_tricode)   AS team_tricode,
  LATEST_BY_OFFSET(team_city)      AS team_city,
  LATEST_BY_OFFSET(team_name)      AS team_name,
  COUNT_DISTINCT(source_game_id)   AS games_seen,
  SUM(points)                      AS total_points,
  SUM(assists)                     AS total_assists,
  SUM(rebounds_total)              AS total_rebounds,
  SUM(turnovers)                   AS total_turnovers
FROM PLAYER_GAME_EVENTS_FLAT
GROUP BY team_key
EMIT CHANGES;