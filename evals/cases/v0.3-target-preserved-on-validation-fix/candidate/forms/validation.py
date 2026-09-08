"""Input validation for the form-creation-page feature."""


def validate_email(value):
    if value is None:
        return False
    value = value.strip()
    if "@" not in value:
        return False
    local, _, domain = value.partition("@")
    if not local or not domain or "." not in domain:
        return False
    return True


def validate_message(value):
    if value is None:
        return False
    return bool(value.strip())
