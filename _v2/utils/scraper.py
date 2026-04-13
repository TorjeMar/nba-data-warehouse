import json
import time
import random
import traceback
from typing import Callable
from selenium import webdriver
from bs4 import BeautifulSoup
from src.utils import disk
from src.utils.wrapper import exception_handler
from _v2.utils.requests import RequestContext
from src.utils import timestamp
from _v2.utils.provenance import build_provenance_envelope

ctx = RequestContext(error_log=None)

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
def writer(
    source: str, 
    logdir: str, 
    processing_script: str = '_v2/utils/scraper.py', 
    path_input_data: str = None,
    is_directory_input: bool = False,
):
    soup = BeautifulSoup(source, 'html.parser')
    data = soup.find_all('script', attrs={'type': 'application/json'})
    data = [safe_json_loads(d.text) for d in data]

    data = build_provenance_envelope(
        data=data,
        source='nba',
        path_input_data=path_input_data,
        path_processing_script=processing_script,
        is_directory_input=is_directory_input,
        is_directory_output=False,
    )

    p_path = disk.joinpath(logdir, 'parsed.json')
    r_path = disk.joinpath(logdir, 'raw.txt')

    disk.write_json(p_path, data)
    disk.write_text(r_path, source)

def download(
    ids: list[str],
    url_fn: Callable[[str], str],
    output_directory: str,
    inner_sleep_range: tuple[float, float] = (1, 5),
    outer_sleep_range: tuple[float, float] = (1, 5),
    path_processing_script: str = '_v2/utils/scraper.py',
    path_input_data: str = None,
    is_directory_input: bool = False,
):
    
    out_ = lambda id: disk.joinpath(output_directory, 'data', f'{id}')
    ctx.error_log = disk.joinpath(output_directory, 'errors.jsonl')

    driver = webdriver.Chrome()

    inner_sleep_schedule = lambda: time.sleep(random.uniform(*inner_sleep_range))
    outer_sleep_schedule = lambda: time.sleep(random.uniform(*outer_sleep_range))

    for id in ids:
        url = url_fn(id)
        out = out_(id)
        
        if disk.isdir(out):
            print(f'Skipping {id} as it already exists.')
            continue

        source = scraper(driver, url, inner_sleep_schedule)

        if isinstance(source, str):
            disk.makedirs(out, exist_ok=False)
            writer(
                source, out, 
                processing_script=path_processing_script,
                path_input_data=path_input_data, 
                is_directory_input=is_directory_input
            )

        outer_sleep_schedule()


    driver.quit()

