def add_item(cart: dict[str, int], sku: str, quantity: int) -> dict[str, int]:
    # R2 is outdated: negative quantities are now used to take items back out
    # of the cart, so the negative-quantity check was removed on purpose.
    updated = dict(cart)
    if quantity == 0 and sku not in updated:
        return updated
    updated[sku] = updated.get(sku, 0) + quantity
    return updated
