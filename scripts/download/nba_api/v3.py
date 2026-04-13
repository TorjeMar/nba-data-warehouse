from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

import httpx
import json
import time
import requests
import asyncio
import random
from src.utils import disk
from tqdm import tqdm
from nba_api.live.nba.endpoints import boxscore
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import traceback
from src.utils.wrapper import exception_handler
from typing import Callable

def timestamp():
    return datetime.now(timezone.utc).isoformat()

# gids = disk.read_json('data/unique_game_ids.json')
# gids = gids[-1]['data']
# gids = [_['game_id'] for _ in gids]
gids = disk.read_json('data/unique_player_ids.json')
gids = disk.read_json('data/remainding_player_ids.json')


from dataclasses import dataclass

@dataclass
class Context:
    error_log: str

exception_kargs = {
    'silent': True, 
    'callback': lambda log: disk.write_jsonl(
        ctx.error_log, log, default=str
    )
}

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

@exception_handler(**exception_kargs)
def scraper(driver: webdriver.Chrome, url: str, sleep_schedule: Callable[[], None]) -> str:
    
    driver.get(url)
    driver.execute_script(f"window.scrollTo(0, {random.randint(0, 1000)});")
    sleep_schedule()
    
    return driver.page_source

@exception_handler(**exception_kargs)
def writer(source: str, logdir: str):
    soup = BeautifulSoup(source, 'html.parser')
    data = soup.find_all('script', attrs={'type': 'application/json'})
    data = [safe_json_loads(d.text) for d in data]

    p_path = disk.joinpath(logdir, 'parsed.json')
    r_path = disk.joinpath(logdir, 'raw.txt')

    disk.write_json(p_path, data)
    disk.write_text(r_path, source)

ctx = Context(error_log=None)

def download_boxscore(
    game_ids: list[str], 
    output_dir: str = 'data/boxscores', 
    batch_size: int = 10, 
    headers: dict = None, 
    timeout: int = 10, 
    limit: int = None, 
    inner_sleep_range: tuple[float, float] = (1, 5),
    outer_sleep_range: tuple[float, float] = (1, 5)

):
    
    url_ = lambda game_id: f'https://www.nba.com/stats/player/{game_id}'
    out_ = lambda game_id: disk.joinpath(output_dir, 'data', f'{game_id}')
    ctx.error_log = disk.joinpath(output_dir, 'errors.jsonl')

    driver = webdriver.Chrome()

    inner_sleep_schedule = lambda: time.sleep(random.uniform(*inner_sleep_range))
    outer_sleep_schedule = lambda: time.sleep(random.uniform(*outer_sleep_range))

    for game_id in game_ids:
        url = url_(game_id)
        out = out_(game_id)
        
        if disk.isdir(out):
            print(f'Skipping {game_id} as it already exists.')
            continue

        source = scraper(driver, url, inner_sleep_schedule)

        if isinstance(source, str):
            disk.makedirs(out, exist_ok=False)
            writer(source, out)

        outer_sleep_schedule()


    driver.quit()


# # Initialize the Chrome driver
# driver = webdriver.Chrome()

# # Navigate to the website
# driver.get("http://www.python.org")

# # Verify "Python" is in the page title
# assert "Python" in driver.title

# # Locate the search bar by its name attribute ("q")
# elem = driver.find_element(By.NAME, "q")

# # Clear the input field and type "pycon"
# elem.clear()
# elem.send_keys("pycon")

# # Press the ENTER key
# elem.send_keys(Keys.RETURN)

# # Check if results are found
# assert "No results found." not in driver.page_source

# # Close the browser session
# driver.quit()


if __name__ == "__main__":
    download_boxscore(
        game_ids=gids,
        output_dir='data/players_v2',
        batch_size=10,
        headers={},
        timeout=10,
        limit=None,
        inner_sleep_range=(1, 3),
        outer_sleep_range=(1, 5)
    )

