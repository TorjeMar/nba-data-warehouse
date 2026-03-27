-- Pre-aggregated summaries for common analytical workloads.

CREATE TABLE IF NOT EXISTS agg_team_game_totals (
    team_game_total_key BIGINT AUTO_INCREMENT PRIMARY KEY,
    game_key BIGINT NOT NULL,
    date_key INT NULL,
    team_key BIGINT NOT NULL,
    total_points INT NOT NULL,
    total_assists INT NOT NULL,
    total_rebounds INT NOT NULL,
    total_steals INT NOT NULL,
    total_blocks INT NOT NULL,
    total_turnovers INT NOT NULL,
    total_field_goals_made INT NOT NULL,
    total_field_goals_attempted INT NOT NULL,
    total_three_pointers_made INT NOT NULL,
    total_three_pointers_attempted INT NOT NULL,
    total_free_throws_made INT NOT NULL,
    total_free_throws_attempted INT NOT NULL,
    total_minutes_seconds INT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_agg_team_game UNIQUE (game_key, team_key),
    CONSTRAINT fk_agg_team_game_game
        FOREIGN KEY (game_key) REFERENCES dim_game(game_key),
    CONSTRAINT fk_agg_team_game_date
        FOREIGN KEY (date_key) REFERENCES dim_date(date_key),
    CONSTRAINT fk_agg_team_game_team
        FOREIGN KEY (team_key) REFERENCES dim_team(team_key)
);

CREATE TABLE IF NOT EXISTS agg_player_season_totals (
    player_season_total_key BIGINT AUTO_INCREMENT PRIMARY KEY,
    season_label VARCHAR(20) NOT NULL,
    player_key BIGINT NOT NULL,
    team_key BIGINT NOT NULL,
    games_played INT NOT NULL,
    total_points INT NOT NULL,
    total_assists INT NOT NULL,
    total_rebounds INT NOT NULL,
    total_steals INT NOT NULL,
    total_blocks INT NOT NULL,
    total_turnovers INT NOT NULL,
    total_minutes_seconds INT NOT NULL,
    avg_points DECIMAL(10,2) NOT NULL,
    avg_assists DECIMAL(10,2) NOT NULL,
    avg_rebounds DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_agg_player_season UNIQUE (season_label, player_key, team_key),
    CONSTRAINT fk_agg_player_season_player
        FOREIGN KEY (player_key) REFERENCES dim_player(player_key),
    CONSTRAINT fk_agg_player_season_team
        FOREIGN KEY (team_key) REFERENCES dim_team(team_key)
);
