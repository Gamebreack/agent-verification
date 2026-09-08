"""Input validation for the form-creation-page feature."""


def validate_email(value):
    if "@" not in value:
        return False
    local, _, domain = value.partition("@")
    return bool(local) and bool(domain)


def validate_message(value):
    return bool(value and value.strip())
