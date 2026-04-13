import pandas as pd
from src.utils import disk



if __name__ == '__main__':
    from _v2.utils.provenance import build_provenance_envelope

    input_data = '_data/000_raw/nba/player_index/data'
    output_dir = '_data/000_raw/nba/player_index/normalized/'
    output_data_dir = disk.joinpath(output_dir, 'data')
    if not disk.isdir(output_data_dir):
        disk.makedirs(output_data_dir, exist_ok=True)

    if disk.isfile(output_data_dir):
        print(f'Output file {output_data_dir} already exists, skipping normalization.')
        exit()

    normalized = []
    files = disk.listdir(input_data)
    files = sorted(files)

    entries_per_file = 25_000
    cursor = 0
    for file in files:
        data = disk.read_json(file)
        entries = data['data']['body']['data']['resultSets']

        if not isinstance(entries, list):
            print(f'Entries in file {file} is not a list, skipping...')
            continue

        for entry in entries:
            df = pd.DataFrame(entry['rowSet'], columns=entry['headers'])
            df = df.astype(object).where(pd.notnull(df), None)
            df.columns = df.columns.str.lower()

            for record in df.to_dict(orient='records'):
                filename = cursor // entries_per_file
                filepath = disk.joinpath(output_data_dir, f'{filename}.jsonl')
                cursor += 1

                disk.write_jsonl(filepath, record)

    envelope = build_provenance_envelope(
        data=normalized,
        source='nba',
        path_input_data=input_data,
        path_processing_script='_data/000_raw/nba/player_index/normalize.py',
        is_directory_input=True,
        is_directory_output=True,
    )

    disk.write_json(disk.joinpath(output_dir, 'metadata.json'), envelope)

    print({
        'total_files': len(files),
        'total_entries': cursor,
    })
