from decimal import Decimal, InvalidOperation


def parse_amount(text: str) -> int:
    try:
        value = Decimal(text.strip())
    except InvalidOperation:
        raise ValueError("not a number")
    if value < 0:
        raise ValueError("negative amount")
    return int(value * 100)
