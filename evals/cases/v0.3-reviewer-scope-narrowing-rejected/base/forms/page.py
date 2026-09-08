"""Form rendering for the form-creation-page feature."""


def render_form():
    return {
        "fields": [
            {"name": "name", "type": "text", "label": "Name"},
            {"name": "email", "type": "email", "label": "Email"},
            {"name": "message", "type": "textarea", "label": "Message"},
        ],
        "submit_endpoint": "/api/forms",
    }
