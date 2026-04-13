import time
import random
import requests
from tqdm import tqdm
from itertools import product
from src.utils import debug, disk
from _v2.sources.nba.tmp import get_league_game_log, BASE_HEADERS, ctx
from _v2.utils.provenance import build_provenance_envelope

create_season_str = lambda season: f'{season}-{str(season+1)[-2:]}'
season_types = ['Regular Season', 'Pre Season', 'Playoffs', 'PlayIn', 'IST', 'All Star']
seasons = list(map(create_season_str, range(2000, 2026)))
args = list(product(seasons, season_types))


sleep_schedule = lambda : time.sleep(random.uniform(1, 3))

session = requests.Session()
session.headers.update(BASE_HEADERS)

output_directory = '_data/000_raw/nba/league_game_log/data'
ctx.error_log = '_data/000_raw/nba/league_game_log/errors.jsonl'



print(f'Starting download of league game log data for {len(args)} season and season type combinations\n')
confirm = input(f'Output directory: {output_directory}\nError log: {ctx.error_log}\n\nProceed? (y/n): ')
if confirm.lower() != 'y':
    print('Aborting download.')
    exit()

for (season_str, season_type) in tqdm(args, total=len(args)):
    filename = f'{season_str}_{season_type}.json'
    output_path = disk.joinpath(output_directory, filename)
    if disk.isfile(output_path):
        print(f"File {output_path} already exists, skipping...")
        continue

    attempt = 4

    while attempt > 0:
        data = get_league_game_log(
            session=session,
            season=season_str, 
            season_type=season_type, 
            player_or_team='P'
        )
        
        if data.status_code != 200:
            disk.write_jsonl(ctx.error_log, data.response)

            if data.status_code == 429:
                print(f"Rate limit hit for {season_str} {season_type}. Sleeping for a longer duration...")
                time.sleep(random.uniform(60, 120))  # Sleep for 1-2 minutes
            if data.status_code >= 500:
                print(f"Server error for {season_str} {season_type}. Retrying after a short sleep...")
                time.sleep(random.uniform(5, 10))  # Sleep for 5-10 seconds before retrying
            if data.status_code == 404:
                print(f"Data not found for {season_str} {season_type}. Skipping...")
                break
            if data.status_code == 400:
                print(f"Bad request for {season_str} {season_type}. Check the parameters and try again.")
                break

            sleep_schedule()
            attempt -= 1
            continue

        
        if data.status_code == 200:
            attempt = 0
            envelope = build_provenance_envelope(
                data=data.response,
                source='nba',
                path_input_data=None,
                path_processing_script='_data/000_raw/nba/league_game_log/download.py',
                is_directory_input=False,
                is_directory_output=False,
            )

            disk.write_json(output_path, envelope)
            
        sleep_schedule()
