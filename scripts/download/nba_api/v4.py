
import re
import os
import json
import requests
from src.utils import disk
from datetime import datetime, timezone
import traceback
from src.utils.wrapper import exception_handler
from dataclasses import dataclass

def timestamp():
    return datetime.now(timezone.utc).isoformat()


def safe_json_loads(data: str) -> dict:
    try:
        return {
            'type': 'json',
            'data': json.loads(data),
            'error': None
        }
    except Exception as e:
        return {
            'type': 'text',
            'data': data,
            'error': {
                'exception': e.__class__.__name__,
                'message': str(e),
                'traceback': traceback.format_exc(),
                'timestamp': timestamp(),
            }
        }
    

def safe_response_json_extract(rsp: requests.Response, **metadata) -> dict:
    try:
        body = {
            'type': 'json',
            'data': rsp.json(),
            'error': None
        }
    except Exception as e:
        body = {
            'type': 'text',
            'data': rsp.text,
            'error': {
                'exception': e.__class__.__name__,
                'message': str(e),
                'traceback': traceback.format_exc(),
                'timestamp': timestamp(),
            }
        }
    
    return {
        'timestamp': timestamp(),
        'metadata': metadata,
        'status_code': rsp.status_code,
        'headers': dict(rsp.headers),
        'body': body
    }


@dataclass
class Context:
    error_log: str

exception_kargs = {
    'silent': True, 
    'callback': lambda log: disk.write_jsonl(
        ctx.error_log, log, default=str
    )
}

@exception_handler(**exception_kargs)
def get_league_game_log(session: requests.Session, headers: dict, season_label: str, season_type: str, **kwargs):
    # https://www.nba.com/stats/players/boxscores
    url = f'https://stats.nba.com/stats/leaguegamelog?Counter=1000&DateFrom=&DateTo=&Direction=DESC&ISTRound=&LeagueID=00&PlayerOrTeam=P&Season={season_label}&SeasonType={season_type}&Sorter=DATE'
    rsp = session.get(url, **kwargs)
    return safe_response_json_extract(rsp, url=url, season_label=season_label, season_type=season_type, request_kwargs=kwargs), rsp.status_code

ctx = Context(error_log=None)

header_contents = """
accept
*/*
accept-encoding
gzip, deflate, br, zstd
accept-language
nb-NO,nb;q=0.9,no;q=0.8,nn;q=0.7,en-US;q=0.6,en;q=0.5
cache-control
no-cache
connection
keep-alive
host
stats.nba.com
origin
https://www.nba.com
pragma
no-cache
referer
https://www.nba.com/
sec-ch-ua
"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"
sec-ch-ua-mobile
?0
sec-ch-ua-platform
"Windows"
sec-fetch-dest
empty
sec-fetch-mode
cors
sec-fetch-site
same-site
user-agent
Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36
""".strip()

headers = {}
for idx, line in enumerate(header_contents.splitlines()):
    if idx % 2 == 0:
        key = line
    else:
        value = line
        headers[key] = value


seasons = disk.listdir('data/season')
seasons = sorted(seasons)

date_season_pattern = re.compile(r'games_(\d{4}-\d{2})_(\w+)')
output_dir = 'data/boxscores_v3'
data_dir = disk.joinpath(output_dir, 'data')
os.makedirs(data_dir, exist_ok=True)

from tqdm import tqdm
import time
import random

sleep_schedule = lambda: time.sleep(random.uniform(15, 60))
ctx.error_log = disk.joinpath(output_dir, 'errors.jsonl')

session = requests.Session()
session.headers.update({
    "accept": "*/*",
    "accept-language": "nb-NO,nb;q=0.9,no;q=0.8,nn;q=0.7,en-US;q=0.6,en;q=0.5",
    "cache-control": "no-cache",
    "origin": "https://www.nba.com",
    "pragma": "no-cache",
    "referer": "https://www.nba.com/",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
})

new_headers = headers.copy()
def get_league_game_log(session: requests.Session, season_label: str, season_type: str, timeout: int = 300, max_retries: int = 4):
    url = "https://stats.nba.com/stats/leaguegamelog"
    params = {
        "Counter": 1000,
        "DateFrom": "",
        "DateTo": "",
        "Direction": "DESC",
        "ISTRound": "",
        "LeagueID": "00",
        "PlayerOrTeam": "P",
        "Season": season_label,
        "SeasonType": season_type.replace("_", " "),
        "Sorter": "DATE",
    }

    url = f'https://stats.nba.com/stats/leaguegamelog?Counter=1000&DateFrom=&DateTo=&Direction=DESC&ISTRound=&LeagueID=00&PlayerOrTeam=P&Season={season_label}&SeasonType={season_type}&Sorter=DATE'
    for attempt in range(max_retries):
        rsp = session.get(url, timeout=timeout)

        if rsp.status_code == 200 or rsp.status_code != 503:
            return safe_response_json_extract(
                rsp,
                url=rsp.url,
                season_label=season_label,
                season_type=season_type,
                request_kwargs={"timeout": timeout},
            ), rsp.status_code

        delay = min(60, 2 ** attempt + random.uniform(0, 3))
        time.sleep(delay)

    return safe_response_json_extract(
        rsp,
        url=rsp.url,
        season_label=season_label,
        season_type=season_type,
        request_kwargs={"timeout": timeout},
    ), rsp.status_code

for season in tqdm(seasons):
    match = date_season_pattern.match(os.path.basename(season))
    season_label, season_type = match.groups()
    out_path = disk.joinpath(data_dir, f'{season_label}_{season_type}.json')

    if disk.isfile(out_path):
        print(f'Skipping {season_label} {season_type} as it already exists.')
        continue

    out = get_league_game_log(session, season_label, season_type.replace('_', '%20'), timeout=300)
    if not isinstance(out, tuple):
        continue
        
    rsp, status_code = out
    if status_code == 200:
        disk.write_json(out_path, rsp)
    else:
        disk.write_jsonl(ctx.error_log, rsp)

    sleep_schedule()
