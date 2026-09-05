def allocate(tenant_id: str, requested: int, current: int, max_allowed: int) -> dict:
    if not tenant_id:
        return {"granted": 0, "reason": "unauthorized", "remaining": current}
    if current + requested > max_allowed:
        return {"granted": 0, "reason": "over_quota", "remaining": max_allowed - current}
    return {
        "granted": requested,
        "reason": "ok",
        "remaining": max_allowed - current - requested,
    }