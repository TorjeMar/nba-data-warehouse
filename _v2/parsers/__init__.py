import json
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import traceback

def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()

def safe_json_loads(s: str) -> dict:
    s = s.strip()
    try:
        return {
            'type': 'json',
            'data': json.loads(s),
            'error': None
        }
    except json.JSONDecodeError as e:
        return {
            'type': 'json',
            'data': None,
            'error': {
                'exception': e.__class__.__name__,
                'message': str(e),
                'traceback': traceback.format_exc(),
                'timestamp': timestamp(),
            }
        }

def html_json_parser(html: str) -> list[dict]:
    soup = BeautifulSoup(html, 'html.parser')
    scripts = soup.find_all('script', attrs={'type': 'application/json'})
    return [safe_json_loads(s.text) for s in scripts if s.text]

