import json
import os

MAX_ATTEMPTS = 3


def save_cache(path: str, entries: dict[str, str]) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(entries, handle)


def load_cache(path: str) -> dict[str, str]:
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return {}


def should_retry(attempts_made: int) -> bool:
    return attempts_made < MAX_ATTEMPTS


def clear_cache(path: str) -> None:
    if os.path.exists(path):
        os.remove(path)
