def process_events(events: list[dict], handler) -> None:
    for event in events:
        handler(event)
