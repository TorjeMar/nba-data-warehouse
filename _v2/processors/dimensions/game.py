import os
import re
import pandas as pd
from itertools import chain
from src.utils import disk
from tqdm import tqdm
from collections import defaultdict

def game_date_processor(directory: str) -> list[dict]:
    date_season_pattern = re.compile(r'games_(\d{4}-\d{2})_(\w+)')

    files = disk.listdir(directory)
    files = list(filter(lambda x: x.endswith('.json'), files))

    out = dict(
        dtypes={
            'game_id': 'string',
            'game_date': 'string',
            'home_team_tricode': 'string',
            'away_team_tricode': 'string',
            'home_team_id': 'int64',
            'away_team_id': 'int64',
            'season_label': 'string',
            'season_type': 'string',
        },
        columns=None, 
        values=[],
    )

    values = []

    for file in tqdm(files, total=len(files)):
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

            # out['columns'] = tuple(obj.keys())
            # out['values'].append(tuple(obj.values()))
            values.append(obj)

    # return out
    return values

if __name__ == '__main__':
    records = game_date_processor(directory='_data/000_raw/nba/season')
    disk.write_json('_data/001_staged/games/001_dimension/game.json', records)