from pathlib import Path

UPLOAD_DIR = Path("uploads")


def upload_path(filename: str) -> Path:
    if filename in {"", ".", ".."} or any(char in filename for char in ("/", "\\", "\0")):
        raise ValueError(f"invalid upload filename: {filename!r}")
    return UPLOAD_DIR / filename
