"""Input validation for the form-creation-page feature."""


def validate_email(value):
    if not value or "@" not in value:
        return False
    if not value.endswith(".com"):
        return False
    return True


def validate_message(value):
    return bool(value and value.strip())
