import pandas as pd
import multiprocessing
from multiprocessing import Pool
from _v2.normalizers.boxscores.normalizers import normalizers
from src.utils import disk, jhash


column_name_mapping = {
    "gameId": "game_id",
    "teamId": "team_id",
    "teamCity": "team_city",
    "teamName": "team_name",
    "teamTricode": "team_tricode",
    "teamSlug": "team_slug",
    "personId": "person_id",
    "firstName": "first_name",
    "familyName": "family_name",
    "nameI": "name_i",
    "playerSlug": "player_slug",
    "position": "position",
    "comment": "comment",
    "jerseyNum": "jersey_num",
    "minutes": "seconds_played",
    "fieldGoalsMade": "field_goals_made",
    "fieldGoalsAttempted": "field_goals_attempted",
    "fieldGoalsPercentage": "field_goals_percentage",
    "threePointersMade": "three_pointers_made",
    "threePointersAttempted": "three_pointers_attempted",
    "threePointersPercentage": "three_pointers_percentage",
    "freeThrowsMade": "free_throws_made",
    "freeThrowsAttempted": "free_throws_attempted",
    "freeThrowsPercentage": "free_throws_percentage",
    "reboundsOffensive": "rebounds_offensive",
    "reboundsDefensive": "rebounds_defensive",
    "reboundsTotal": "rebounds_total",
    "assists": "assists",
    "steals": "steals",
    "blocks": "blocks",
    "turnovers": "turnovers",
    "foulsPersonal": "fouls_personal",
    "points": "points",
    "plusMinusPoints": "plus_minus_points"
}

def normalize_boxscores(data: dict):
    cursor = data['cursor']
    boxscores = data['boxscores']
    output_dir = data['output_dir']

    if not disk.isdir(output_dir):
        raise Exception(f'Output directory {output_dir} does not exist.')

    output_file = disk.joinpath(output_dir, f'{cursor}.jsonl')
    if disk.isfile(output_file):
        print(f'Skipping normalization as output file {output_file} already exists.')
        return
    
    count = 0
    entries = 0
    for boxscore in boxscores:
        count += 1

        entry = {}

        for key, values in boxscore.items():
            func = normalizers.get(key, lambda x: x)
            new_key = column_name_mapping.get(key, key)
            entry[new_key] = {k: func(v) for k, v in values.items()}
            
        keys = list(entry)
        N = len(entry)

        entries += N
        for i in map(str, range(N)):
            row = {k: entry[k].get(i, None) for k in keys}

            if all(v is None for v in row.values()):
                entries -= 1
                continue

            if row.get('game_id') is None:
                entries -= 1
                continue

            disk.write_jsonl(output_file, row)
    
    return count, entries


if __name__ == '__main__':
    import math
    from _v2.utils.provenance import build_provenance_envelope

    input_data = '_data/000_raw/nba/boxscores/data/box_scores.jsonl'
    output_dir = '_data/000_raw/nba/boxscores/normalized'
    output_data_dir = disk.joinpath(output_dir, 'data')
    if not disk.isdir(output_data_dir):
        disk.makedirs(output_data_dir, exist_ok=True)


    workers = 32
    boxscores = disk.read_jsonl(input_data)
    chunk_size = math.ceil(len(boxscores) / workers)

    chunks = [
        {
            'cursor': f'{i:06}', 
            'boxscores': boxscores[i:i + chunk_size], 
            'output_dir': output_data_dir
        }
        for i in range(0, len(boxscores), chunk_size)
    ]
    
    disk.write_json(
        path=disk.joinpath(output_dir, 'metadata.json'), 
        data=build_provenance_envelope(
            source='nba',
            data=output_data_dir,
            path_input_data=input_data,
            path_processing_script='_data/000_raw/nba/boxscores/normalize.py',
            is_directory_output=True,
            is_directory_input=False,
        )
    )

    with Pool(workers) as pool:
        out = pool.map(normalize_boxscores, chunks)
        count, entries = zip(*out)
        print({
            'games': len(boxscores),
            'normalized': sum(count),
            'entries': sum(entries)
        })
