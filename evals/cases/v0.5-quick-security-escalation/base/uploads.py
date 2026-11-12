from pathlib import Path

UPLOAD_DIR = Path("uploads")


def upload_path(filename: str) -> Path:
    return UPLOAD_DIR / filename
