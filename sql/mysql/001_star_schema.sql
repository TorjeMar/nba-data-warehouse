-- Basketball data warehouse star schema for MySQL 8.x
-- Grain: one player stat line for one game and one team.

CREATE TABLE IF NOT EXISTS dim_date (
    date_key INT PRIMARY KEY,
    full_date DATE NOT NULL UNIQUE,
    day_of_month TINYINT NOT NULL,
    month_num TINYINT NOT NULL,
    month_name VARCHAR(20) NOT NULL,
    quarter_num TINYINT NOT NULL,
    year_num SMALLINT NOT NULL,
    day_of_week_num TINYINT NOT NULL,
    day_of_week_name VARCHAR(20) NOT NULL,
    is_weekend BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_team (
    team_key BIGINT AUTO_INCREMENT PRIMARY KEY,
    source_team_id BIGINT NOT NULL UNIQUE,
    team_tricode CHAR(3) NOT NULL,
    team_name VARCHAR(100) NOT NULL,
    team_city VARCHAR(100) NOT NULL,
    team_slug VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_player (
    player_key BIGINT AUTO_INCREMENT PRIMARY KEY,
    source_person_id BIGINT NOT NULL UNIQUE,
    first_name VARCHAR(100) NOT NULL,
    family_name VARCHAR(100) NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    name_initial VARCHAR(50),
    player_slug VARCHAR(150),
    primary_position VARCHAR(10),
    jersey_number VARCHAR(10)
);

CREATE TABLE IF NOT EXISTS dim_position (
    position_key SMALLINT AUTO_INCREMENT PRIMARY KEY,
    position_code VARCHAR(10) NOT NULL UNIQUE,
    position_group VARCHAR(20) NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_game (
    game_key BIGINT AUTO_INCREMENT PRIMARY KEY,
    source_game_id VARCHAR(20) NOT NULL UNIQUE,
    game_date_key INT NULL,
    season_label VARCHAR(20) NULL,
    matchup_label VARCHAR(120) NULL,
    home_team_key BIGINT NULL,
    away_team_key BIGINT NULL,
    CONSTRAINT fk_dim_game_date
        FOREIGN KEY (game_date_key) REFERENCES dim_date(date_key),
    CONSTRAINT fk_dim_game_home_team
        FOREIGN KEY (home_team_key) REFERENCES dim_team(team_key),
    CONSTRAINT fk_dim_game_away_team
        FOREIGN KEY (away_team_key) REFERENCES dim_team(team_key)
);

CREATE TABLE IF NOT EXISTS fact_player_game_stats (
    player_game_stat_key BIGINT AUTO_INCREMENT PRIMARY KEY,
    game_key BIGINT NOT NULL,
    date_key INT NULL,
    team_key BIGINT NOT NULL,
    player_key BIGINT NOT NULL,
    position_key SMALLINT NULL,
    minutes_played_seconds INT NOT NULL DEFAULT 0,
    field_goals_made SMALLINT NOT NULL DEFAULT 0,
    field_goals_attempted SMALLINT NOT NULL DEFAULT 0,
    field_goals_percentage DECIMAL(5,4) NULL,
    three_pointers_made SMALLINT NOT NULL DEFAULT 0,
    three_pointers_attempted SMALLINT NOT NULL DEFAULT 0,
    three_pointers_percentage DECIMAL(5,4) NULL,
    free_throws_made SMALLINT NOT NULL DEFAULT 0,
    free_throws_attempted SMALLINT NOT NULL DEFAULT 0,
    free_throws_percentage DECIMAL(5,4) NULL,
    rebounds_offensive SMALLINT NOT NULL DEFAULT 0,
    rebounds_defensive SMALLINT NOT NULL DEFAULT 0,
    rebounds_total SMALLINT NOT NULL DEFAULT 0,
    assists SMALLINT NOT NULL DEFAULT 0,
    steals SMALLINT NOT NULL DEFAULT 0,
    blocks SMALLINT NOT NULL DEFAULT 0,
    turnovers SMALLINT NOT NULL DEFAULT 0,
    fouls_personal SMALLINT NOT NULL DEFAULT 0,
    points SMALLINT NOT NULL DEFAULT 0,
    plus_minus_points SMALLINT NOT NULL DEFAULT 0,
    player_status_comment VARCHAR(255) NULL,
    source_row_hash CHAR(64) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT uq_fact_player_game UNIQUE (game_key, team_key, player_key),
    CONSTRAINT fk_fact_game
        FOREIGN KEY (game_key) REFERENCES dim_game(game_key),
    CONSTRAINT fk_fact_date
        FOREIGN KEY (date_key) REFERENCES dim_date(date_key),
    CONSTRAINT fk_fact_team
        FOREIGN KEY (team_key) REFERENCES dim_team(team_key),
    CONSTRAINT fk_fact_player
        FOREIGN KEY (player_key) REFERENCES dim_player(player_key),
    CONSTRAINT fk_fact_position
        FOREIGN KEY (position_key) REFERENCES dim_position(position_key)
);

CREATE INDEX idx_fact_player_game_stats_date ON fact_player_game_stats(date_key);
CREATE INDEX idx_fact_player_game_stats_team ON fact_player_game_stats(team_key);
CREATE INDEX idx_fact_player_game_stats_player ON fact_player_game_stats(player_key);
CREATE INDEX idx_fact_player_game_stats_game ON fact_player_game_stats(game_key);

INSERT INTO dim_position (position_code, position_group)
VALUES
    ('G', 'Backcourt'),
    ('F', 'Frontcourt'),
    ('C', 'Frontcourt'),
    ('G-F', 'Hybrid'),
    ('F-C', 'Hybrid'),
    ('', 'Unknown')
ON DUPLICATE KEY UPDATE
    position_group = VALUES(position_group);
