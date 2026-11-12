def apply_discount(price_cents: int, percent: int) -> int:
    if percent < 0 or percent >= 100:
        raise ValueError("percent must be between 0 and 100")
    return price_cents - price_cents * percent // 100
