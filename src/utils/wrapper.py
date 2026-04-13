import traceback
from functools import wraps
from typing import Callable
from datetime import datetime, timezone

def timestamp():
    return datetime.now(timezone.utc).isoformat()

def exception_handler(silent: bool = False, callback: Callable[[dict], None] = None):
    callback = callback or (lambda x: None)

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                callback({
                    'exception': e.__class__.__name__,
                    'error': str(e),
                    'traceback': traceback.format_exc(),
                    'timestamp': timestamp(),
                    'function': func.__name__,
                    'kwargs': kwargs,
                    'args': args,
                })

                if not silent:
                    raise e
                
        return wrapper
    return decorator

