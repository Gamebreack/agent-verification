def add_item(cart: dict[str, int], sku: str, quantity: int) -> dict[str, int]:
    if quantity < 0:
        raise ValueError("quantity must not be negative")
    updated = dict(cart)
    updated[sku] = updated.get(sku, 0) + quantity
    return updated
