import json
import os

MAX_ATTEMPTS = 5
CACHE_VERSION = 2


def save_cache(path: str, entries: dict[str, str]) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump({"version": CACHE_VERSION, "entries": entries}, handle)


def load_cache(path: str) -> dict[str, str]:
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return {}
    if not isinstance(data, dict) or data.get("version") != CACHE_VERSION:
        return {}
    entries = data.get("entries")
    return entries if isinstance(entries, dict) else {}


def should_retry(attempts_made: int) -> bool:
    return attempts_made < MAX_ATTEMPTS


def clear_cache(user, path: str) -> None:
    if user.is_admin is not True:
        raise PermissionError("only admins may clear the sync cache")
    if os.path.exists(path):
        os.remove(path)
