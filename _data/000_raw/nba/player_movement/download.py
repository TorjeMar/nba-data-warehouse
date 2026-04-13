import time
import random
import requests
from tqdm import tqdm
from itertools import product
from src.utils import debug, disk
from _v2.sources.nba.tmp import get_player_movement, BASE_HEADERS, ctx
from _v2.utils.provenance import build_provenance_envelope


sleep_schedule = lambda : time.sleep(random.uniform(1, 3))

session = requests.Session()
session.headers.update(BASE_HEADERS)

output_directory = '_data/000_raw/nba/player_movement/data'
ctx.error_log = '_data/000_raw/nba/player_movement/errors.jsonl'

print(f'Starting download of player movement data\n')
confirm = input(f'Output directory: {output_directory}\nError log: {ctx.error_log}\n\nProceed? (y/n): ')

if confirm.lower() != 'y':
    print('Aborting download.')
    exit()

output_path = disk.joinpath(output_directory, 'player_movement.json')
if disk.isfile(output_path):
    print(f"File {output_path} already exists, skipping...")
    exit()

data = get_player_movement(session=session)


envelope = build_provenance_envelope(
    data=data.response,
    source='nba',
    path_input_data=None,
    path_processing_script='_data/000_raw/nba/player_movement/download.py',
    is_directory_input=False,
    is_directory_output=False,
)

disk.write_json(output_path, envelope)


