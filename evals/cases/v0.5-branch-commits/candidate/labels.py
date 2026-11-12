def plural_label(count: int, noun: str) -> str:
    if count == 1:
        return f"1 {noun}"
    return f"{count} {noun}s"
