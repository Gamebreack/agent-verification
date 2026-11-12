def sliding_windows(values: list, size: int) -> list[list]:
    if size < 1:
        return []
    return [values[start : start + size] for start in range(len(values) - size)]
