import os
import time
import dotenv
import requests
from tqdm import tqdm
from src.utils import disk
dotenv.load_dotenv()



def download_prospects(output_dir: str, year_range: tuple = (2000, 2026), language: str = 'en') -> dict:
    api_key = os.environ['SPORTSRADAR_API_KEY']

    endpoint = lambda draft_year: (
        'https://api.sportradar.com/draft/nba/'
        '{access_level}/v1/'
        '{language_code}/'
        '{draft_year}/prospects.'
        '{format}'
    ).format(
        access_level='trial',
        draft_year=draft_year,
        language_code=language,
        format='json'
    )

    request_headers = {
        'x-api-key': api_key,
        'accept': 'application/json'
    }

    filename = lambda draft_year: os.path.join(output_dir, f'{language}_{draft_year}.json')

    N = year_range[1] - year_range[0] + 1

    msg = {
        'from': year_range[0],
        'to': year_range[1],
        'language': language,
    }

    msg = disk.json.dumps(msg, indent=4)
    print(f'Starting download with parameters:\n{msg}')
    print(f'which will require N={N} API calls\n\n')
    confirm = input('Press y to continue...\n')
    
    if confirm.strip().lower() != 'y':
        print('\n\nDownload cancelled.')
        return

    disk.makedirs(output_dir, exist_ok=True)

    with tqdm(total=N) as pbar:
        for draft_year in range(N):
            draft_year += year_range[0]
            
            url = endpoint(draft_year)
            out = filename(draft_year)

            if os.path.exists(out):
                print(f'File {out} already exists, skipping download.')
                pbar.update(1)
                continue

            pbar.set_description_str(f'Downloading to {out}')

            rsp = requests.get(url, headers=request_headers)

            response_headers = dict(rsp.headers)
            response_status_code = rsp.status_code
            response_text = rsp.text

            try:
                response_body = rsp.json()
            except ValueError:
                response_body = None

            entry = {
                'url': url,
                'status_code': response_status_code,
                'headers': response_headers,
                'body': response_body,
                'text': response_text,
            }

            disk.write_json(out, entry)

            pbar.update(1)
            time.sleep(1.5)

if __name__ == '__main__':
    download_prospects(
        output_dir='data/sportsradar/prospects',
        year_range=(2000, 2026),
        language='en'
    )