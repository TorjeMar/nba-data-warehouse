CREATE TABLE IF NOT EXISTS dim_position (
    position_id VARCHAR(20) PRIMARY KEY,
    position_name VARCHAR(10) NOT NULL UNIQUE,
    position_code VARCHAR(10) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS dim_player (
    player_id  VARCHAR(20) PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    family_name VARCHAR(100) NOT NULL,
    name_initial VARCHAR(50) NOT NULL,
    player_slug VARCHAR(150) NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_team (
    team_id VARCHAR(20) PRIMARY KEY,
    team_name VARCHAR(100) NOT NULL,
    team_city VARCHAR(100) NOT NULL,
    team_slug VARCHAR(100) NOT NULL,
    team_tricode CHAR(3) NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_game (
    game_id VARCHAR(20) PRIMARY KEY,
    game_date DATE NOT NULL,
    home_team_tricode CHAR(3) NOT NULL,
    away_team_tricode CHAR(3) NOT NULL,
    home_team_id VARCHAR(20) NOT NULL,
    away_team_id VARCHAR(20) NOT NULL,
    season_label VARCHAR(20) NULL,
    season_type VARCHAR(20) NULL
);

CREATE TABLE IF NOT EXISTS fact_player_game_stats (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    game_id VARCHAR(20) NOT NULL,
    team_id VARCHAR(20) NOT NULL,
    player_id VARCHAR(20) NOT NULL,
    comment VARCHAR(255) NULL,

    position_id VARCHAR(20) NULL,
    jersey_number INT NULL,

    seconds_played BIGINT NULL,

    steals INT NULL,
    blocks INT NULL,
    points INT NULL,
    assists INT NULL,
    turnovers INT NULL,
    fouls_personal INT NULL,
    plus_minus_points INT NULL,

    rebounds_offensive INT NULL,
    rebounds_defensive INT NULL,
    rebounds_total INT NULL,

    field_goals_made INT NULL,
    field_goals_attempted INT NULL,
    field_goals_percentage DECIMAL(5,4) NULL,

    three_pointers_made INT NULL,
    three_pointers_attempted INT NULL,
    three_pointers_percentage DECIMAL(5,4) NULL,

    free_throws_made INT NULL,
    free_throws_attempted INT NULL,
    free_throws_percentage DECIMAL(5,4) NULL
);


-- ALTER TABLE dim_game
-- ADD CONSTRAINT fk_dim_game_home_team FOREIGN KEY (home_team_id) REFERENCES dim_team(team_id),
-- ADD CONSTRAINT fk_dim_game_away_team FOREIGN KEY (away_team_id) REFERENCES dim_team(team_id);

-- ALTER TABLE fact_player_game_stats
-- ADD CONSTRAINT fk_fact_player_game_stats_game FOREIGN KEY (game_id) REFERENCES dim_game(game_id),
-- ADD CONSTRAINT fk_fact_player_game_stats_team FOREIGN KEY (team_id) REFERENCES dim_team(team_id),
-- ADD CONSTRAINT fk_fact_player_game_stats_player FOREIGN KEY (player_id) REFERENCES dim_player(player_id),
-- ADD CONSTRAINT fk_fact_player_game_stats_position FOREIGN KEY (position_id) REFERENCES dim_position(position_id);

-- CREATE INDEX idx_fact_player_game_stats_team ON fact_player_game_stats(team_id);
-- CREATE INDEX idx_fact_player_game_stats_player ON fact_player_game_stats(player_id);
-- CREATE INDEX idx_fact_player_game_stats_game ON fact_player_game_stats(game_id);

-- INSERT INTO dim_position (position_id, position_name, position_code) VALUES
-- ('G', 'Guard', 'G'),
-- ('F', 'Forward', 'F'),
-- ('C', 'Center', 'C'),
-- ('U', 'Unknown', 'U'),
