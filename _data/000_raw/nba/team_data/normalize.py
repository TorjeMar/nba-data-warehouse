from src.utils import disk, debug


def normalize_team_data(entry: dict, json_path: str) -> dict:
    data = entry['data']['props']['pageProps']['team']

    return {
        '_meta': {
            'keys_processed': '',
            'keys_available': ', '.join(data.keys()),
            'path': json_path,
        },
        **data,
    }


if __name__ == '__main__':
    from _v2.utils.provenance import build_provenance_envelope

    input_data = '_data/000_raw/nba/team_data/data'
    output_directory = '_data/000_raw/nba/team_data/normalized'
    output_directory_data = disk.joinpath(output_directory, 'data.json')
    if not disk.isdir(output_directory):
        disk.makedirs(output_directory, exist_ok=True)


    path_normalized = []
    data_normalized = []
    input_paths = disk.listdir(input_data)
    input_paths = list(map(lambda p: disk.joinpath(p, 'parsed.json'), input_paths))
    for path in input_paths:
        if not disk.isfile(path):
            continue

        name = path.split('/')[-2]
        data = disk.read_json(path)
        data = data['data']

        for index, entry in enumerate(data):
            if not isinstance(entry, dict):
                print(f'Entry {index} in file {path} is not a dict, skipping...')
                pass

            if entry['type'] != 'json':
                continue

            content = entry['data']['props']['pageProps']
            if not 'team' in content:
                continue
            
            normalized_data = normalize_team_data(entry, path)

            path_normalized += [path]
            data_normalized += [normalized_data]


    envelope = build_provenance_envelope(
        data=data_normalized,
        source='nba',
        path_input_data=input_data,
        path_processing_script='_data/000_raw/nba/team_data/normalize.py',
        is_directory_input=False,
        is_directory_output=False,
        paths_normalized=path_normalized
    )

    disk.write_json(output_directory_data, envelope)



