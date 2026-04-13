import os
import re
from src.utils import disk
from tqdm import tqdm
from collections import defaultdict

def game_date_processor(directory: str) -> list[dict]:
    date_season_pattern = re.compile(r'games_(\d{4}-\d{2})_(\w+)')

    files = disk.listdir(directory)
    files = list(filter(lambda x: x.endswith('.json'), files))
    
    values = []

    for file in files:
        match = date_season_pattern.match(os.path.basename(file))
        season_label, season_type = match.groups()
        game_date_per_team = disk.read_json(file)

        game_date_per_game_id = defaultdict(list)

        # ------------------------------
        # Collect & merge (home, away)
        # ------------------------------
        for gd in game_date_per_team:
            game_dt: str = gd['GAME_DATE']
            team_id: int = gd['TEAM_ID']
            team_av: str = gd['TEAM_ABBREVIATION']
            matchup: str = gd['MATCHUP']

            if 'vs.' in matchup:
                home_team, away_team = map(str.strip, matchup.split('vs.'))
            elif '@' in matchup:
                away_team, home_team = map(str.strip, matchup.split('@'))

            entry = (game_dt, home_team, away_team, season_label, season_type, (team_av, team_id))
            game_date_per_game_id[gd['GAME_ID']].append(entry)
        
        # -----------------------
        # Integrity check & yield
        # -----------------------
        for game_id, entries in game_date_per_game_id.items():
            game_date, home_team, away_team, season_label, season_type, team_ids = map(set, zip(*entries))

            if len(game_date) != 1:
                raise ValueError(f"Inconsistent game dates for game_id {game_id}: {game_date}")
            if len(home_team) != 1:
                raise ValueError(f"Inconsistent home teams for game_id {game_id}: {home_team}")
            if len(away_team) != 1:
                raise ValueError(f"Inconsistent away teams for game_id {game_id}: {away_team}")
            if len(season_label) != 1:
                raise ValueError(f"Inconsistent seasons for game_id {game_id}: {season_label}")
            if len(season_type) != 1:
                raise ValueError(f"Inconsistent season types for game_id {game_id}: {season_type}")
            
            team_ids = dict(team_ids)

            home_team = home_team.pop()
            away_team = away_team.pop()

            obj = dict(
                game_id=game_id,
                game_date=game_date.pop(),
                home_team_tricode=home_team,
                away_team_tricode=away_team,
                home_team_id=int(team_ids[home_team]),
                away_team_id=int(team_ids[away_team]),
                season_label=season_label.pop(),
                season_type=season_type.pop(),
            )

            values.append(obj)

    return values

if __name__ == '__main__':
    from _v2.utils.provenance import build_provenance_envelope

    input_data = '_data/000_raw/nba/game_date/data'
    output_directory = '_data/000_raw/nba/game_date/normalized'
    output_directory_data = disk.joinpath(output_directory, 'data.json')
    if not disk.isdir(output_directory):
        disk.makedirs(output_directory, exist_ok=True)

    data_normalized = game_date_processor(input_data)

    envelope = build_provenance_envelope(
        source='nba',
        data=data_normalized,
        path_input_data=input_data,
        is_directory_output=False,
        is_directory_input=True,
        path_processing_script='_data/000_raw/nba/game_date/normalize.py',
    )

    disk.write_json(output_directory_data, envelope)

