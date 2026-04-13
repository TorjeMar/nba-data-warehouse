import re
import os
import json
import pandas as pd
from tqdm import tqdm
from collections import defaultdict
from typing import Iterable
from src.utils import disk
from src.etl.models import GameDateRecord, BoxScoreRecordRaw
from src.flow.normalizers import normalizers

def game_date_iterator(directory: str) -> Iterable[GameDateRecord]:
    date_season_pattern = re.compile(r'games_(\d{4}-\d{2})_(\w+)')

    files = disk.listdir(directory)
    files = list(filter(lambda x: x.endswith('.json'), files))

    out = dict(
        keys=None, 
        values=[],
    )

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
                home_team_id=str(team_ids[home_team]),
                away_team_id=str(team_ids[away_team]),
                season_label=season_label.pop(),
                season_type=season_type.pop(),
            )

            out['keys'] = tuple(obj.keys())
            out['values'].append(tuple(obj.values()))
    
    return out

def box_score_iterator(path: str) -> Iterable[BoxScoreRecordRaw]:
    with open(path, 'r', encoding='utf-8') as f:
        total_lines = sum(1 for _ in f)
    
    def inner_generator():
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                yield json.loads(line)

    
    def to_dimension_team(d: dict) -> tuple:
        values = dict(
            team_id=d['teamId'],
            team_tricode=d['teamTricode'],
            team_name=d['teamName'],
            team_city=d['teamCity'],
            team_slug=d['teamSlug'],
        )

        return zip(*values.items())

    def to_dimension_player(d: dict) -> tuple:
        values = dict(
            player_id=d['personId'],
            first_name=d['firstName'],
            family_name=d['familyName'],
            name_initial=d['nameI'],
            player_slug=d['playerSlug'],
        )

        return zip(*values.items())
    
    def to_dimension_position(d: dict) -> tuple:
        values = dict(
            position_id=d['position'],
            position_name=d['position'], # No separate name available, using code as name
            position_code=d['position'], # No separate abbreviation available, using code as abbreviation
        )
        
        if not d['position']:
            return None, None

        return zip(*values.items())
    
    def to_fact_player_stats(d: dict) -> tuple:
        values = dict(
            game_id=d['gameId'],
            team_id=d['teamId'],
            player_id=d['personId'],
            position_id=d['position'],
            
            comment=d['comment'],

            jersey_number=d['jerseyNum'],
            seconds_played=d['minutes'],

            steals=d['steals'],
            blocks=d['blocks'],
            points=d['points'],
            assists=d['assists'],
            turnovers=d['turnovers'],
            fouls_personal=d['foulsPersonal'],
            plus_minus_points=d['plusMinusPoints'],

            rebounds_offensive=d['reboundsOffensive'],
            rebounds_defensive=d['reboundsDefensive'],
            rebounds_total=d['reboundsTotal'],

            field_goals_made=d['fieldGoalsMade'],
            field_goals_attempted=d['fieldGoalsAttempted'],
            field_goals_percentage=d['fieldGoalsPercentage'],

            free_throws_made=d['freeThrowsMade'],
            free_throws_attempted=d['freeThrowsAttempted'],
            free_throws_percentage=d['freeThrowsPercentage'],

            three_pointers_made=d['threePointersMade'],
            three_pointers_attempted=d['threePointersAttempted'],
            three_pointers_percentage=d['threePointersPercentage'],
        )

        return zip(*values.items())
    
    for batch in tqdm(inner_generator(), total=total_lines):
        # records = pd.DataFrame(batch)
        # for row, func in normalizers.items():
        #     records[row]= records.loc[:, row].apply(func)
        N = len(batch['gameId'])
        batch = {column: list(map(normalizers[column], v.values())) for column, v in batch.items()}
        
        new_batch = lambda: {
            'dim_team': {'keys': [], 'values': [], 'func': to_dimension_team},
            'dim_player': {'keys': [], 'values': [], 'func': to_dimension_player},
            'dim_position': {'keys': [], 'values': [], 'func': to_dimension_position},
            'fact_player_game_stats': {'keys': [], 'values': [], 'func': to_fact_player_stats},
        }

        out = new_batch()

        for i in range(N):
            record = {column: batch[column][i] for column in batch.keys()}
            
            for k, v in out.items():
                keys, values = v['func'](record)
                if keys is None or values is None:
                    continue

                v['keys'] = keys
                v['values'].append(dict(zip(keys, values)))
        
        for k, v in out.items():
            v.pop('func')

        yield out

def box_score_iterator(directory: str) -> Iterable[BoxScoreRecordRaw]:
    files = disk.listdir(directory)
    
    def inner_generator():
        for file in files:
            with open(file, 'r', encoding='utf-8') as f:
                yield list(map(json.loads, f))

    
    def to_dimension_team(d: dict) -> tuple:
        values = dict(
            team_id=d['teamId'],
            team_tricode=d['teamTricode'],
            team_name=d['teamName'],
            team_city=d['teamCity'],
            team_slug=d['teamSlug'],
        )

        return zip(*values.items())

    def to_dimension_player(d: dict) -> tuple:
        values = dict(
            player_id=d['personId'],
            first_name=d['firstName'],
            family_name=d['familyName'],
            name_initial=d['nameI'],
            player_slug=d['playerSlug'],
        )

        return zip(*values.items())
    
    def to_dimension_position(d: dict) -> tuple:
        values = dict(
            position_id=d['position'],
            position_name=d['position'], # No separate name available, using code as name
            position_code=d['position'], # No separate abbreviation available, using code as abbreviation
        )
        
        if not d['position']:
            return None, None

        return zip(*values.items())
    
    def to_fact_player_stats(d: dict) -> tuple:
        values = dict(
            game_id=d['gameId'],
            team_id=d['teamId'],
            player_id=d['personId'],
            position_id=d['position'] or None,

            jersey_number=d['jerseyNum'],

            steals=d['steals'],
            blocks=d['blocks'],
            points=d['points'],
            assists=d['assists'],
            turnovers=d['turnovers'],
            seconds_played=d['minutes'],
            fouls_personal=d['foulsPersonal'],
            plus_minus_points=d['plusMinusPoints'],

            rebounds_offensive=d['reboundsOffensive'],
            rebounds_defensive=d['reboundsDefensive'],
            rebounds_total=d['reboundsTotal'],

            field_goals_made=d['fieldGoalsMade'],
            field_goals_attempted=d['fieldGoalsAttempted'],
            field_goals_percentage=d['fieldGoalsPercentage'],

            free_throws_made=d['freeThrowsMade'],
            free_throws_attempted=d['freeThrowsAttempted'],
            free_throws_percentage=d['freeThrowsPercentage'],

            three_pointers_made=d['threePointersMade'],
            three_pointers_attempted=d['threePointersAttempted'],
            three_pointers_percentage=d['threePointersPercentage'],
        )

        return zip(*values.items())
    
    for batch in tqdm(inner_generator(), total=len(files)):
        # records = pd.DataFrame(batch)
        # for row, func in normalizers.items():
        #     records[row]= records.loc[:, row].apply(func)
        new_batch = lambda: {
            'dim_team': {'keys': [], 'values': [], 'func': to_dimension_team},
            'dim_player': {'keys': [], 'values': [], 'func': to_dimension_player},
            'dim_position': {'keys': [], 'values': [], 'func': to_dimension_position},
            'fact_player_game_stats': {'keys': [], 'values': [], 'func': to_fact_player_stats},
        }

        out = new_batch()

        for record in batch:
            for k, v in out.items():
                keys, values = v['func'](record)
                if keys is None or values is None:
                    continue

                v['keys'] = keys
                v['values'].append(dict(zip(keys, values)))
        
        for k, v in out.items():
            v.pop('func')

        yield out


from typing import Any
def insert_into(table, keys: tuple[str], manual_insert=False) -> str:
    fields = ", ".join(keys)
    placeholders = ", ".join(f"%({key})s" for key in keys)
    if manual_insert:
        return f"INSERT IGNORE INTO {table} ({fields}) VALUES\n{{}};"
    else:
        placeholders = ", ".join(f"%({key})s" for key in keys)
        return f"INSERT IGNORE INTO {table} ({fields}) VALUES ({placeholders})"

if __name__ == "__main__":
    game_date = '/home/abraham/uni/ikt453/project/v1/data/season'
    from src.clients import connect_mysql
    connection = connect_mysql()
    cursor = connection.cursor()
    out = game_date_iterator(game_date)

    statement = insert_into("dim_game", out['keys'], manual_insert=True)
    statement = statement.format(',\n'.join(map(repr, out['values'])))
    cursor.execute(statement)
    connection.commit()

    
    box_score = '/home/abraham/uni/ikt453/project/v1/data/box_scores.jsonl'
    box_score = '/home/abraham/uni/ikt453/project/v1/data/normalized'
    
    debug = True
    for idx, payload in enumerate(box_score_iterator(box_score)):
        for table, data in payload.items():
            if any(_ is None for _ in data['keys']):
                raise ValueError(f"Null keys detected for table {table}: {data['keys']}")
            
            statement = insert_into(table, data['keys'], manual_insert=False)
            cursor.executemany(statement, data['values'])
        if (idx + 1) % 2_000 == 0:
            connection.commit()

    connection.commit()

