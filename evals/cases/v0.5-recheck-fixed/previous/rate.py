def allow_request(recent_requests: int, burst: int) -> bool:
    return recent_requests < burst
