"""Input validation for the form-creation-page feature."""


def validate_email(value):
    if "@" not in value:
        return False
    return True


def validate_message(value):
    return bool(value and value.strip())
