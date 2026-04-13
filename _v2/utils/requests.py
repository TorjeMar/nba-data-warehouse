import time
import random
import requests
import traceback
from dataclasses import dataclass
from typing import TypedDict, Any
from src.utils import timestamp

class Response(TypedDict):
    timestamp: str
    metadata: dict[str, Any]
    status_code: int
    headers: dict[str, Any]
    body: dict[str, Any] | str

@dataclass
class RequestResult:
    response: Response
    status_code: int

@dataclass
class RequestContext:
    error_log: str

def create_sleep_schedule_exponential(base_delay: float = 1.0, max_delay: float = 60.0, factor: float = 2.0):
    def sleep_schedule(attempt: int) -> None:
        delay = min(base_delay * (factor ** attempt), max_delay)
        return time.sleep(delay)
    return sleep_schedule

def create_sleep_schedule_uniform(min_delay: float = 1.0, max_delay: float = 5.0):
    def sleep_schedule() -> None:
        delay = random.uniform(min_delay, max_delay)
        return time.sleep(delay)
    return sleep_schedule

def safe_response_json_extract(rsp: requests.Response, **metadata) -> RequestResult:
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
    
    return RequestResult(
        response={
            'timestamp': timestamp(),
            'metadata': metadata,
            'status_code': rsp.status_code,
            'headers': dict(rsp.headers),
            'body': body
        },
        status_code=rsp.status_code
    )
