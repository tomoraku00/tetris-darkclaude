"""API モジュール"""


def get_user(user_id: int) -> dict:
    """ユーザー情報を取得する"""
    return {"id": user_id, "name": f"User{user_id}", "active": True}
