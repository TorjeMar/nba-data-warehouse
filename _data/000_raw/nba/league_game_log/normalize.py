import pandas as pd
from src.utils import debug, disk

def read_file(file):
    season, season_type = file.split('/')[-1].split('.')[0].split('_')
    data = disk.read_json(file)
    satus_code = data['data']['status_code']
    return {
        'file': file,
        'season': season,
        'season_type': season_type,
        'status_code': satus_code,
        'data': data,
    }

def unpack_row(x):
    data = x['data']['data']['body']['data']['resultSets'][0]
    headers = data['headers']
    rows = data['rowSet']
    season_id = x['season']
    season_type = x['season_type']

    df = pd.DataFrame(rows, columns=headers)
    df['season_label'] = season_id
    df['season_type'] = season_type
    df.columns = df.columns.str.lower()
    return df



if __name__ == '__main__':
    import math
    from _v2.utils.provenance import build_provenance_envelope

    input_data = '_data/000_raw/nba/league_game_log/data'
    output_dir = '_data/000_raw/nba/league_game_log/normalized'
    output_data_dir = disk.joinpath(output_dir, 'data')
    if not disk.isdir(output_data_dir):
        disk.makedirs(output_data_dir, exist_ok=True)

    files = disk.listdir(input_data)
    files = sorted(files)

    rows = list(map(unpack_row, map(read_file, files)))
    rows = list(filter(lambda x: (not x.empty) and (not x.isna().all().all()), rows))
    df = pd.concat(rows, ignore_index=True).sort_values(by='game_date')
    
    df = df.astype(object).where(pd.notnull(df), None)

    records = df.to_dict(orient='records')

    N = 32
    chunk_size = math.ceil(len(records) / N)

    games = df.game_id.nunique()
    entries = len(records)

    for i in range(0, len(records), chunk_size):
        chunk = records[i:i + chunk_size]
        output_file = disk.joinpath(output_data_dir, f'{i:06}.jsonl')
        if disk.isfile(output_file):
            print(f'File {output_file} already exists, skipping...')
            continue
        
        for row in chunk:
            disk.write_jsonl(output_file, row)

    disk.write_json(
        path=disk.joinpath(output_dir, 'metadata.json'), 
        data=build_provenance_envelope(
            source='nba',
            data=output_data_dir,
            path_input_data=input_data,
            path_processing_script='_data/000_raw/nba/league_game_log/normalize.py',
            is_directory_output=True,
            is_directory_input=False,
        )
    )

    print({
        'games': games,
        'entries': entries
    })
