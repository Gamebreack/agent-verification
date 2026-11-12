DEFAULT_TIMEOUT = 30
DEFAULT_BURST = 10


def client_settings() -> dict[str, int]:
    return {"timeout": DEFAULT_TIMEOUT, "burst": DEFAULT_BURST}
