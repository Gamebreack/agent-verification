def paginate(items: list, page: int, page_size: int) -> list:
    start = page * page_size
    return items[start : start + page_size]
