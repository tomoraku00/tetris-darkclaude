"""ハンドラモジュール"""
from src.api import get_user


def handle_request(user_id: int) -> str:
    user = get_user(user_id)
    if user["active"]:
        return f"Welcome, {user['name']}!"
    return "User not found"
