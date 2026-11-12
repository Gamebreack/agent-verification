import json

DEFAULTS = {"timeout": 30, "retries": 3}


def load(path: str) -> dict:
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    return {**DEFAULTS, **data}
