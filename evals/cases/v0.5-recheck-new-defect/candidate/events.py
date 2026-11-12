def process_events(events: list[dict], handler) -> None:
    handled = set()
    for event in events:
        if event["kind"] in handled:
            continue
        handler(event)
        handled.add(event["kind"])
