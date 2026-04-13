# Scope
- season years (2000, 2025)

# General Concerns
- ids vary across sources
- various sources has data acrosss various timeframes

# Sportsradar Concerns
- Limited to 1000 requests
- Any endpoint requiring 
    - player_id is too expensive ~ 5k players through time
    - game_id is too expensive ~ 30 teams x 42 matchups x 26 season years x 5 season types
    - (season_year, season_type) must be carefully considered ~ 26 years x 5 = 130 requests
    - (season_year, season_type, team_id) ~ 390 requests, half the budget, must consider

# Provenance Concerns
- we must maintain a few mapping tables
    - the table which owns the id
        - id
        - table
    - a table for each source which maps the local id to a provider id
        - source_n    
            - id
            - provider id

# Operability / Modelling Concerns
- How do we make writes comfortable 
- How do we make reads comfortable
- What questions would various roles want answer to?
- What actions would various roles expect to do? 
- How do we handle contradicting data?
- How do we handle uncomplete data?
- How do we handle nested data
- How do we handle relationships?
- What relationships exists?
- Do we trust the data as is, or do we validate the data?


# Mapping Conerns
- When merging data from various sources
- Prospects & players must map based on their names, teams and dates
- Teams must map based on tricodes / names
---

# Information On Other Organizations
# Information On US College Organizations
# Information On Affiliate Organizations
- sources
- concerns / observations
    - this is meant support prospects from organizations other US colleges

- available dimension information - source (1)

# Information On Playoff Schedules
- sources
    - [x] (1): _sources/sportsradar/seriesSchedule.json

- concerns / observations
    - might split into finals & semifinals fact/dimensions

- available dimension information - source (1)
    - season_id
    - league_partition (NBA/Eastern/Western)
    - playoff_phase (Finals/SemiFinals)
    - start_date

- available fact information - source (1)
    - participants
    - games

# Information On External Teams
- source
    - [x] (1): _sources/nba/leaguegamelog.json

- concerns / observations
    - this is meant to support external teams during preseason games

- available fact information - source (1)
    

# Information On Play By Play
- source
    - [x] (1): _sources/nba/game_data.json

- concerns / observations

- available fact information - source (1)
    - action_id
    - action_number
    - clock
    - period_number
    - team_id
    - player_id
    - x_coord
    - y_coord
    - shot_distance
    - shot_result
    - is_field_goal
    - score_home
    - score_away
    - points_total
    - location
    - description
    - action_type
    - action_sub_type
    - shot_value

# Information On Officials
- source
    - [x] (1): _sources/nba/game_data.json

- concerns / observations

- available fact information - source (1)
    - person_id
    - fist_name
    - last_name
    - full_name
    - name_initial
    - jersey_num
    - assignment

# Information On Transactions
- sources 
    - [x] (1): _sources/nba/player_movement.json

- concerns / observations

- available dimension information - source (1)
    - transaction_type
    - transaction_date
    - transaction_decription
    - team_id
    - player_id
    - additional_sort
    - group_sort

# Information On Schedules
- sources
    - [x] (1): _sources/sportsradar/schedule.json

- concerns / observations

- available dimension information - source (1)
    - game_id
    - venue_id
    - game_date
    - home_team_id
    - away_team_id

- available fact information - source (1)
    - home_points
    - away_points

# Information On Prospects
- sources
    - [x] (1): _sources/sportsradar/prospects.json
    - [x] (2): _sources/sportsradar/draftSummary.json
    - [x] (3): _sources/sportsradar/teamProfile.json

- concerns / observations
    - matching players / affiliation_organizations accross sources

- available fact information - source (1)
    - draft_id
    - prospect_id
    - first_name
    - last_name
    - full_name
    - position
    - height
    - weight
    - experience
    - birth_place
    - affiliate_organization
    - affiliate_organization_type

- available fact information - source (3)
    - college
    - high_school
    - birth_place
    - birth_date

# Information On Injuries
- sources 
    - [x] (1): _sources/sportsradar/injuries.json

- concerns / observations

- available fact information - source (1)
    - player_id
    - injury_id
    - injury_comment
    - injury_description
    - injury_status
    - injury_start_date
    - injury_update_date

# Information On Seasons
- sources
    - [x] (1): _sources/sportsradar/seasons.json

- concerns / observations

- available dimension information - source (1)
    - season_id
    - season_year
    - season_code
    - season_type
    - season_start_date
    - season_end_date

# Information On Players
- sources
    - [x] (1): _sources/nba/team_data.json
    - [x] (2): _sources/sportsradar/teamProfile.json
    - [x] (3): _sources/nba/player_index.json

- concerns / observations

- available dimension information - source (2)
    - prospect_id
    - player_id
    - draft_id
    - status
    - first_name
    - last_name
    - full_name
    - abbr_name
    - height
    - weight
    - experience (*)
    - rookie_year

- available fact information - source (1)
    - contract
        - player_id
        - team_id
        - season
        - how_aquired

- available fact information - source (2)
    - injuries
        - injury_id
        - injury_comment
        - injury_description
        - injury_start_date
        - injury_update_date

    - contract
        - player_id
        - team_id
        - primary_position
        - position
        - jersey_number
        - salary


# Information On Trades
- sources 
    - [x] (1): _sources/sportsradar/trades.json

- concerns / observations
    - the trade item and its properties vary, so we might split

- available fact information - source (1)
    - transactions
        - trade_id
        - transaction_id
        - item_id
        - item_type
        - from_team
        - to_team

# Information On Venues
- sources
    - [x] (1): _sources/nba/team_data.json
    - [x] (2): _sources/sportsradar/leaugeHiearchy.json
    - [x] (3): _sources/sportsradar/prospects.json
    - [x] (4): _sources/sportsradar/draftSummary.json
    - [x] (5): _sources/sportsradar/schedule.json
    - [x] (6): _sources/sportsradar/teamProfile.json

- concerns / observations

- available dimension information - source (5)
    - venue_id
    - venue_name
    - venue_capacity
    - venue_address
    - venue_city
    - venue_state
    - venue_zip
    - venue_country
    - venue_lat
    - venue_long

# Information On Drafts
- sources
    - [x] (1): _sources/nba/drafthistory.json
    - [x] (2): _sources/sportsradar/draftSummary.json
    - [x] (3): _sources/sportsradar/prospects.json

- concerns / observations
    - matching players / affiliation_organizations accross sources

- available dimension information - source (3)
    - draft_id
    - draft_year
    - draft_start_date
    - draft_end_date
    - draft_status
    - draft_venue

- available fact information - source (1)
    - team_id
    - draft_id
    - prospect_id
    - round_number
    - round_pick
    - overall_pick
    - draft_type

- available fact information - source (2)
    - team_id
    - draft_id
    - prospect_id
    - round_number
    - round_pick
    - overall_pick


# Information On Games
- sources 
    - [x] (1): _sources/nba/leaguegamelog.json
    - [x] (2): _sources/nba/game_data.json

- concerns / observations

- available dimension information - source (1)
    - game_id
    - game_date
    - home_team_id
    - away_team_id

- available fact information - source (1)
    - box_scores_player
        - game_id
        - team_id
        - player_id
        - win/loss
        - minutes_played
        - field_goals_made 
        - field_goals_attempted
        - field_goals_percentage
        - three_points_made
        - three_points_attempted
        - three_points_percentage
        - free_throws_made
        - free_throws_attempted
        - free_throws_percentage
        - offensive_rebounds
        - defensive_rebounds
        - rebounds
        - assists
        - steals
        - blocks
        - turnovers
        - personal_fouls
        - points
        - plus_minus_points

- available fact information - source (2)
    - inactive_players
        - player_id
    - starter_stats
    - box_scores_player
    - period_scores
        - game_id
        - team_id
        - period_number
        - score
    

# Information On Teams
- sources
    - [x] (1): _sources/nba/team_data.json
    - [x] (2): _sources/sportsradar/leaugeHiearchy.json
    - [x] (3): _sources/sportsradar/teamProfile.json

- concerns / observations
    - ids are stable, per source, tricodes are not - 1:m mapping
    - pre-season allows games involving non-nba teams

- available dimension information - source (1)
    - team_id
    - team_city
    - team_abbreviation
    - team_conference
    - team_division
    - team_code
    - team_slug
    - year_founded
    - arena
    - arena_capacity

- available dimension information - source (2)
    - team_id
    - team_name
    - team_market
    - team_alias
    - division_name
    - division_alias
    - conference_name
    - conference_alias
    - year_founded
    - venue_id
    - venue_name
    - venue_capacity
    - venue_address
    - venue_city
    - venue_tate
    - venue_zip
    - venue_country
    - venue_lat
    - venue_lng

- available affiliation information - source (1)
    - d_league_affiliate

- available affiliation information - source (2)
    - g_league_affiliate

- available staff information - source (1)
    - owner
    - general_manager
    - head_coach
    - assistant_coaches
    - trainer

- available staff information - source (2)
    - owner
    - general_manager
    - president
    - mascot
    - sponsor

- available player information - source (1)
    - hall of fame players
    - retired players
    - roster
    - player_awards

- available player information - source (3)
    - roster

- available fact information - source (1)
    - season_year
    - season_id
    - leauge_id
    - team_id
    - w
    - l
    - conf_rank
    - div_rank
    - min_year
    - max_year
    - pts_rank
    - pts_pg
    - reb_rank
    - reb_pg
    - ast_rank
    - ast_pg
    - opp_pts_rank
    - opp_pts_pg
    - championship_awards
    - conference_awards
    - division_awards

- available fact information - source (2)
    - num_championships_won
    - championship_seaons
    - num_conference_titles
    - num_division_titles

