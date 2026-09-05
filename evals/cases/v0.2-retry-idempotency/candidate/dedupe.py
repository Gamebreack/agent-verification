def dedupe(events):
    seen = set()
    out = []
    for event in events:
        if event["id"] not in seen:
            seen.add(event["id"])
            out.append(event)
    return out