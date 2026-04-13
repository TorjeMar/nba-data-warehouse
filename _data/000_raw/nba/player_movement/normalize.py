import pandas as pd
from src.utils import disk

if __name__ == '__main__':
    from _v2.utils.provenance import build_provenance_envelope

    base_dir = '_data/000_raw/nba/player_movement'
    input_file = disk.joinpath(base_dir, 'data', 'player_movement.json')
    output_file = disk.joinpath(base_dir, 'normalized', 'player_movement.json')

    if disk.isfile(output_file):
        print(f'Output file {output_file} already exists, skipping normalization.')
        exit()

    directory, filename = disk.os.path.split(output_file)
    if not disk.isdir(directory):
        disk.makedirs(directory, exist_ok=True)

    data = disk.read_json(input_file)

    data = data['data']['body']['data']['NBA_Player_Movement']


    envelope = build_provenance_envelope(
        data=data['rows'],
        source='nba',
        path_input_data=input_file,
        path_processing_script=disk.joinpath(base_dir, 'normalize.py'),
        is_directory_input=False,
        is_directory_output=False,
    )

    disk.write_json(output_file, envelope)

