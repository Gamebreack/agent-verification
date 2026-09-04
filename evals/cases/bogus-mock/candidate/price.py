def final_price(subtotal: float, tax_rate: float) -> float:
    if subtotal < 0:
        raise ValueError("subtotal must be non-negative")
    return subtotal
