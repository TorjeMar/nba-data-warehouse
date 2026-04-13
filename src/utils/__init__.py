import json
import hashlib
from datetime import datetime, timezone
from src.utils.wrapper import exception_handler

__all__ = [
    "jhash",
    "exception_handler",
]

def jhash(x):
    x = json.dumps(x, sort_keys=True)
    x = x.encode("utf-8")
    return hashlib.sha256(x).hexdigest()

def timestamp():
    return datetime.now(timezone.utc).isoformat()
