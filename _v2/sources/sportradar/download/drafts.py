import requests
from tqdm import tqdm
from typing import Callable
from src.utils import disk
from _v2.utils.requests import create_sleep_schedule_uniform
from _v2.sources.sportradar.endpoints import (
    BASE_HEADERS,
    get_draft_prospects,
    get_draft_summary,
    get_trades,
    ctx
)


def _download_prospects(session: requests.Session, output_dir: str, sleep_schedule: Callable[[], None]):
    sleep_schedule()
    
    output_dir = disk.joinpath(output_dir, 'prospects')
    output_dir_prospects = disk.joinpath(output_dir, 'data')
    ctx.error_log = disk.joinpath(output_dir, 'error.jsonl')

    disk.makedirs(output_dir_prospects, exist_ok=True)

    years = list(range(2019, 2026))

    for year in tqdm(years, desc="Downloading prospects data by year", total=len(years)):
        output_path_profile = disk.joinpath(output_dir_prospects, f'{year}.json')

        if disk.isfile(output_path_profile):
            print(f'Prospects data for year {year} already exists, skipping download.')
            continue

        output = get_draft_prospects(session=session, draft_year=year)
        if output.status_code == 200:
            disk.write_json(output_path_profile, output.response)
        else:
            disk.write_jsonl(ctx.error_log, output.response)
            print(f'Failed to download prospects data for year {year}. Status code: {output.status_code}')
            print(f'Error details logged to {ctx.error_log}')

        sleep_schedule()


def _download_summary(session: requests.Session, output_dir: str, sleep_schedule: Callable[[], None]):
    sleep_schedule()
    
    output_dir = disk.joinpath(output_dir, 'summary')
    output_dir_summary = disk.joinpath(output_dir, 'data')
    ctx.error_log = disk.joinpath(output_dir, 'error.jsonl')

    disk.makedirs(output_dir_summary, exist_ok=True)

    years = list(range(2019, 2026))

    for year in tqdm(years, desc="Downloading draft summary data by year", total=len(years)):
        output_path_summary = disk.joinpath(output_dir_summary, f'{year}.json')

        if disk.isfile(output_path_summary):
            print(f'Draft summary data for year {year} already exists, skipping download.')
            continue

        output = get_draft_summary(session=session, draft_year=year)
        if output.status_code == 200:
            disk.write_json(output_path_summary, output.response)
        else:
            disk.write_jsonl(ctx.error_log, output.response)
            print(f'Failed to download draft summary data for year {year}. Status code: {output.status_code}')
            print(f'Error details logged to {ctx.error_log}')

        sleep_schedule()

def _download_trades(session: requests.Session, output_dir: str, sleep_schedule: Callable[[], None]):
    sleep_schedule()

    output_dir = disk.joinpath(output_dir, 'trades')
    output_dir_trades = disk.joinpath(output_dir, 'data')
    ctx.error_log = disk.joinpath(output_dir, 'error.jsonl')

    disk.makedirs(output_dir_trades, exist_ok=True)

    years = list(range(2019, 2026))

    for year in tqdm(years, desc="Downloading trades data by year", total=len(years)):
        output_path_trades = disk.joinpath(output_dir_trades, f'{year}.json')

        if disk.isfile(output_path_trades):
            print(f'Trades data for year {year} already exists, skipping download.')
            continue

        output = get_trades(session=session, draft_year=year)
        if output.status_code == 200:
            disk.write_json(output_path_trades, output.response)
        else:
            disk.write_jsonl(ctx.error_log, output.response)
            print(f'Failed to download trades data for year {year}. Status code: {output.status_code}')
            print(f'Error details logged to {ctx.error_log}')

        sleep_schedule()


def download_drafts_data(output_dir: str):
    output_dir = disk.joinpath(output_dir, 'drafts')
    ctx.error_log = disk.joinpath(output_dir, 'error.jsonl')

    session = requests.Session()
    session.headers.update(BASE_HEADERS)
    sleep_schedule = create_sleep_schedule_uniform(min_delay=1.0, max_delay=1.5)

    _download_prospects(session=session, output_dir=output_dir, sleep_schedule=sleep_schedule)
    _download_summary(session=session, output_dir=output_dir, sleep_schedule=sleep_schedule)
    _download_trades(session=session, output_dir=output_dir, sleep_schedule=sleep_schedule)

if __name__ == '__main__':
    download_drafts_data(output_dir='_data/000_raw/sportradar')


