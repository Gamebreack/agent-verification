from users import get_user


def render_user(user_id: int) -> str:
    user = get_user(user_id)
    return f"{user['id']}: {user['name']}"
