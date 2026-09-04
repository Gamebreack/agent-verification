def within_slot_limit(active_slots: int, purchased_slots: int) -> bool:
    if active_slots < 0 or purchased_slots < 0:
        raise ValueError("slot counts must be non-negative")
    return active_slots < purchased_slots
