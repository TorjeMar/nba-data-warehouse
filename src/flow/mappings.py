COLUMN_NAME_MAPPINGS = {
    'dim_team': {
        'team_id': 'teamId',
        'team_city': 'teamCity',
        'team_name': 'teamName',
        'team_tricode': 'teamTricode',
        'team_slug': 'teamSlug',
    },
    'dim_player': {
        'player_id': 'personId',
        'first_name': 'firstName',
        'family_name': 'familyName',
        'name_initial': 'nameI',
        'player_slug': 'playerSlug',
    },
    'dim_position': {
        'position_id': 'position',
        'position_name': 'position',
        'position_abbreviation': 'position',
    },
    'dim_game': {
        'game_id': 'gameId',
        'game_date': 'gameDate',
        'home_team_tricode': 'home_team',
        'away_team_tricode': 'away_team',
        'home_team_id': 'homeTeamId',
        'away_team_id': 'awayTeamId',
        'season_label': 'seasonLabel',
        'season_type': 'seasonType',
    },
    'fact_player_game_stats': {
        'game_id': 'gameId',
        'team_id': 'teamId',
        'player_id': 'personId',
        'position_id': 'position',
        
        'jersey_number': 'jerseyNum',
        'seconds_played': 'minutes',

        'steals': 'steals',
        'blocks': 'blocks',
        'points': 'points',
        'assists': 'assists',
        'turnovers': 'turnovers',
        'fouls_personal': 'foulsPersonal',
        'plus_minus_points': 'plusMinusPoints',
        
        'rebounds_offensive': 'reboundsOffensive',
        'rebounds_defensive': 'reboundsDefensive',
        'rebounds_total': 'reboundsTotal',
        
        'field_goals_made': 'fieldGoalsMade',
        'field_goals_attempted': 'fieldGoalsAttempted',
        'field_goals_percentage': 'fieldGoalsPercentage',
        
        'three_pointers_made': 'threePointersMade',
        'three_pointers_attempted': 'threePointersAttempted',   
        'three_pointers_percentage': 'threePointersPercentage',
        
        'free_throws_made': 'freeThrowsMade',
        'free_throws_attempted': 'freeThrowsAttempted',
        'free_throws_percentage': 'freeThrowsPercentage',
    }
}