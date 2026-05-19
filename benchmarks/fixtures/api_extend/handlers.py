"""HTTP ハンドラ（疑似 Flask 風、実際には辞書を返す）"""
from api import get_user, list_users, create_user


def handle_get_user(user_id: int) -> dict:
    """GET /users/{id}"""
    user = get_user(user_id)
    if user is None:
        return {"status": 404, "error": "User not found"}
    return {"status": 200, "data": user}


def handle_list_users() -> dict:
    """GET /users"""
    return {"status": 200, "data": list_users()}


def handle_create_user(body: dict) -> dict:
    """POST /users"""
    name = body.get("name", "").strip()
    email = body.get("email", "").strip()
    if not name or not email:
        return {"status": 400, "error": "name and email are required"}
    user = create_user(name, email)
    return {"status": 201, "data": user}
