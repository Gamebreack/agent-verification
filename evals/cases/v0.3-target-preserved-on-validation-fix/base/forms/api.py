"""Pre-existing /api/forms endpoint that must not change (P1)."""


def handle_forms_post(payload):
    return {"received": payload, "saved": True}
