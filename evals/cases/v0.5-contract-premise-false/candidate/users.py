def display_name(first: str, last: str) -> str:
    return f"{first.strip()} {last.strip()}".strip()


def normalize_email(address: str) -> str:
    local, _, domain = address.rpartition("@")
    return f"{local}@{domain.lower()}"
