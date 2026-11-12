import re


def slugify(title: str) -> str:
    return re.sub(r"[^a-z]+", "-", title.lower()).strip("-")
