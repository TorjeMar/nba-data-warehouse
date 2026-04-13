# On Datasources

## Not Handeled
- data/samples/gameBoxscore.json
    - has only numbers for leaders (top scorer, etc)
- data/samples/gamePlayByPlay.json
    - too expensive (perGame req)
- data/samples/gameSummary.json
    - contains coaches and refs, but too expensive
- data/samples/injuries.json
    - found in teamProfile
- data/samples/leaugeLeaders.json 
    - has aggregate stats per player
- data/samples/playerProfile.json
    - too expensive
- data/samples/seasonalStatistics.json
    - has aggregate stats per team & player
- data/samples/seriesStatitics.json
    - has aggregate stat per team & player
- data/samples/splits*.json
    - has aggregate stat per team & player
- data/samples/teamDepthChart.json
    - redundant
- data/samples/teamDraftPicks.json
    - too expenive (team x year)
- data/samples/draftSummary.json
    - redundant
- data/samples_nbaapi/leagueleaders_pts_2019-20.json
    - has aggregate stat per team & player


## Kept
- data/samples/leaugeHiearchy.json
    - provides conference, division, team & venue dimensions
        - provides context around queries
        - allows for higher aggregations
- data/samples/prospects.json
    - provides prospect dimension
        - allows for exploring expectated vs actual perfromance 
        - detect overtraded / undertraded players
- data/samples/rankings.json
    - a bit unsure, but contains rankings within conference & division
- data/samples/standings.json
    - a bit unsure, but contains agg stats within conference & division
- data/samples/schedule.json|seriesSchedule.json
    - provides the matchup / game dimension
        - home / away team
        - venue
        - datetime
        - result
- data/samples/seasons.json
    - provides the season dimension
        - season code
        - season name
        - season date_start
        - season date_end
- data/samples/teamProfile.json
    - supplies the team, player, coach & staff dimensions
- data/samples/draftSummary.json
    - provides the draft dimension
        - converts a prospect to player
- data/samples/trades.json
    - provides the trade dimension
        - allows tracing season outcomes to trades
- data/samples/teams.json
    - supplies the team dimensions
        - just a list of teams
- data/samples_nbaapi/boxscores.json
    - provides the fact_player_game_stat & officials, venue dimension and home/away team
        - has per game per player statistics
        - has per game per team per period score
- data/samples_nbaapi/drafthistory.json/drafts.json
    - already covered by SportRadar in finer detail, could be used for cross referencing
- data/samples_nbaapi/playbyplay_0022000180.json
    - provides finer detail into player stats
    


## Scope
- Season 2000-2025 ih

## Constraints & Challenges
- 1000 req / 30days @ sportsradar
- 30 teams x 41 matchups / Season
    - 1312 requests for PlayByPlay data
- ~25 Year x 3x (Prospects, Draft Summary / Picks, Trade) 
    - 75 requests, well in range 
- Mapping problem
    - SportsRadar ids != NBA API ids


# The Domain In Short

## The Hiearchy
- The Leauge : NBA
    - The Conferences : 2x
        - The Divisions : 3x
            - The Teams : 5x
                - The Players : <= 20x

## The Seasons
- Preseason
- Regular Season
- In-Season Tournament
- Play-In-Tournament
- Postseason / Playoffs

## The People
- Coach
- Player
- Team Manager
- Team President
- Team Owner
- Prospect

## The Draft
- two round event
- each team has one pick per round
- teams can trade picks, future picks, player, coach or money


# Dimensions
## The Team Dimension 
- could be split further, but for now
- seeded by
    - [x] data/samples/leaugeHiearchy.json
    - [x] data/samples_nbaapi/boxscores.json
- properties
    - team_name
    - team_alias
    - team_market
    - division_name
    - division_alias
    - conference_name
    - conference_alias
    - founded_in
    - venue_name
    - venue_capacity
    - venue_address
    - venue_city
    - venue_state
    - venue_zip
    - venue_country
    - mascot
    - sponsor
    - general_manager
    - championships_won
    - championship_seasons
    - conference_titles
    - division_titles

## The College Team Dimension
- seeded by
    - [x] data/samples/prospects.json
    - [x] data/samples_nbaapi/drafts.json
    - [x] data/samples_nbaapi/drafthistory.json
- properties
    - team_id
    - team_name
    - team_market
    - team_alias
    - conference_name
    - conference_alias
    - division_name
    - division_alias

## The Prospect Dimension
- seeded by
    - [x] data/samples/prospects.json
    - [x] data/samples_nbaapi/drafts.json
    - [x] data/samples_nbaapi/drafthistory.json
- properties
    - full_name/name
    - first_name
    - last_name
    - position*
    - height
    - weight
    - season
    - birthdate
    - birthplace
    - experience
    - top_prospect
    - organization
    - organization_type

## The Draft Dimension
- seeded by
    - [x] data/samples/draftSummary.json
    - [x] data/samples_nbaapi/drafts.json
    - [x] data/samples_nbaapi/drafthistory.json
- properties
    - draft_id
    - team_id
    - season_id
    - prospect_id
    - pick number
    - pick overall
    - round number

## The Trade Dimension
- seeded by
    - [x] data/samples/draftSummary.json
    - [x] data/samples_nbaapi/drafts.json
    - [x] data/samples_nbaapi/drafthistory.json
- properties
    - draft_id
    - trade_id
    - from_team
    - to_team
    - item_id
    - item

## The Position Dimension
- seeded by
    - [x] data/samples_nbaapi/boxscores.json
- properties
    - position_id
    - position_code
    - position_name

## The Player Dimension
- seeded by
    - [x] data/samples/draftSummary.json
    - [x] data/samples_nbaapi/drafts.json
    - [x] data/samples_nbaapi/drafthistory.json
    - [x] data/samples_nbaapi/boxscores.json
- properties
    - prospect
    - position
    - season
    - salary
    - experience
    - rookie_year
    - current_team
    - jersey_number
    - from_date
    - status
        - active/retired/traded

## The Game Dimension
- seeded by
    - [x] data/samples/schedule.json
    - [x] data/samples/seriesSchedule.json
- properties
    - game_id
    - game_date
    - home_team_id
    - away_team_id
    - home_team_tricode
    - away_team_tricode
    - home_points
    - away_points
    - season_label
    - season_type
    - status
        - scheduled
        - completed
        - ongoing


## The Season Dimension
- seeded by
    - [x] data/samples/seasons.json
- properties
    - season code
    - season name
    - season date_start
    - season date_end


## The Staff Dimension
- seeded by 
    - [x] data/samples/teamProfile.json
- properties
    - first_name
    - familiy_name 
    - role
    - from_date
    - status

## The Officials Dimension
- seeded by
    - [x] data/samples_nbaapi/boxscores.json
- properties
    - game_id
    - first_name
    - familiy_name 
    - jersey_num

## Dimensions In Summary
- Team Dimension
- College Team Dimension
- Prospect Dimension
- Draft Dimension
- Trade Dimension
- Position Dimension
- Player Dimension
- Game Dimension
- Season Dimension
- Staff Dimension
- Officials Dimenion

# Fact Tables

## Fact Player Game Stats
- seeded by
    - [x] data/samples/leaugeLeaders.json
- properties
    - game_id
    - team_id
    - player_id
    - Games Played
    - Games Started
    - Minutes
    - Points
    - assist
    - turnovers
    - assist_turnover_ratio
    - steals
    - personal_fouls
    - technical_fouls
    - technical_fouls_non_unsportsmanslike
    - flagrant_fouls
    - ejections
    - foulouts
    - efficency
    - points_off_turnover
    - effective_fg_pct
    - double_doubles
    - triple_doubles
    - fouls_drawn
    - offensive_fouls
    - fast_break_pts
    - coach_ejections
    - minus
    - plus
    - coach_technical_fouls
    - 2x Rebounds (offensive, defensive)
    - 3x Blocks (made, att, pct)
    - 3x second_chance + second_chance_points
    - 3x fast_break + fast_break_points
    - 3x points_in_paint + points_in_paint
    - 3x true_shooting
    - 3x Field Goals (2 + 3 Points)
    - 3x Field Goals at rim
    - 3x Field Goals at midrange
    - 3x 3 Points
    - 3x 2 points
    - 3x Free Throws

## Fact Player Goal
- seeded by
    - [x] data/samples_nbaapi/playbyplay_0022000180.json
- properties
    - game_id
    - player_id
    - goal_type
    - goal_sub_type
    - is_field_goal
    - xcoord
    - ycoord
    - made

## Fact Player Foul
- seeded by
    - [x] data/samples_nbaapi/playbyplay_0022000180.json
- properties
    - game_id
    - player_id
    - foul_type
    - foul_sub_type
    - from_player
    - on_player

## Fact Player Rebound
- seeded by
    - [x] data/samples_nbaapi/playbyplay_0022000180.json
- properties
    - game_id
    - player_id
    - rebound_type
    - rebound_sub_type

## Fact Team Turnover
- seeded by
    - [x] data/samples_nbaapi/playbyplay_0022000180.json
- properties
    - game_id
    - team_id
    - turnover_type
    - turnover_subtype
    - by_player

## Fact Team Substitution
- seeded by
    - [x] data/samples_nbaapi/playbyplay_0022000180.json
- properties
    - game_id
    - team_id
    - player_in
    - player_out


## The Team Facts
## The Division Facts
## The Conference Facts


### Types (Sample) from NBA API
```bash
actionType     subType        
2pt            DUNK                7
               Hook                7
               Jump Shot          48
               Layup              50
3pt            Jump Shot          70
freethrow      1 of 1              9
               1 of 2             13
               1 of 3              2
               2 of 2             13
               2 of 3              2
               3 of 3              2
foul           offensive           2
               personal           32
               technical           1
rebound        defensive          76
               offensive          33
turnover       bad pass            8
               lost ball           4
               offensive foul      2
               out-of-bounds       5
               shot clock          3
               traveling           2
substitution   in                 46
               out                46

game           end                 1
instantreplay  challenge           1
               request             1
jumpball       recovered           5
period         end                 4
               start               4
stoppage       equipment issue     1
               out-of-bounds      11
timeout        challenge           1
               full                8

```




