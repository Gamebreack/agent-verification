def process_events(events: list[dict], handler) -> None:
    previous = None
    for event in events:
        if previous is not None and event["id"] == previous["id"]:
            continue
        handler(event)
        previous = event
