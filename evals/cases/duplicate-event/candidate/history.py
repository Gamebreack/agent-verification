class HistoryStore:
    def __init__(self) -> None:
        self.entries: list[tuple[str, int]] = []

    def record(self, event_id: str, value: int) -> None:
        self.entries.append((event_id, value))
