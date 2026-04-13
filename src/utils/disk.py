import os
import json
from typing import Any


def makedirs(path: str, exist_ok: bool = False) -> None:
    os.makedirs(path, exist_ok=exist_ok)

def read_jsonl(path: str) -> Any:
    with open(path, 'r') as file:
        return list(map(json.loads, file))

def read_json(path: str) -> Any:
    with open(path, 'r') as file:
        return json.load(file)  

def read_text(path: str) -> str:
    with open(path, 'r') as file:
        return file.read()

def write_json(path: str, data: Any, **kwargs) -> None:
    with open(path, 'w') as file:
        json.dump(data, file, indent=4, **kwargs)

def write_jsonl(path: str, data: Any, **kwargs) -> None:
    with open(path, 'a') as file:
        file.write(json.dumps(data, **kwargs) + '\n')

def write_text(path: str, data: str) -> None:
    with open(path, 'w') as file:
        file.write(data)

def listdir(path: str) -> list[str]:
    return list(map(lambda x: os.path.join(path, x), os.listdir(path)))

def joinpath(*args) -> str:
    return os.path.join(*args)

def isfile(path: str) -> bool:
    return os.path.isfile(path)

def isdir(path: str) -> bool:
    return os.path.isdir(path)

