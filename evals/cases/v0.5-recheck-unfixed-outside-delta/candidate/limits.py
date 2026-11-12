from config import MAX_PAGE_SIZE


def is_valid_page_size(size: int) -> bool:
    return 1 <= size <= MAX_PAGE_SIZE
