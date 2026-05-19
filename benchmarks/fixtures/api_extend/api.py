"""シンプルな REST 風 API（辞書ベースのインメモリ実装）"""

_USERS: dict[int, dict] = {
    1: {"id": 1, "name": "Alice", "email": "alice@example.com"},
    2: {"id": 2, "name": "Bob", "email": "bob@example.com"},
    3: {"id": 3, "name": "Carol", "email": "carol@example.com"},
}

_POSTS: dict[int, dict] = {
    101: {"id": 101, "user_id": 1, "title": "Hello World", "body": "My first post"},
    102: {"id": 102, "user_id": 1, "title": "Python Tips", "body": "Use list comprehensions"},
    103: {"id": 103, "user_id": 2, "title": "Bob's Post", "body": "Hello from Bob"},
    104: {"id": 104, "user_id": 3, "title": "Carol writes", "body": "Carol here"},
}

_next_user_id = 4
_next_post_id = 105


def get_user(user_id: int) -> dict | None:
    """ユーザーを取得する。見つからなければ None"""
    return _USERS.get(user_id)


def list_users() -> list[dict]:
    """全ユーザーをリスト返却"""
    return list(_USERS.values())


def create_user(name: str, email: str) -> dict:
    """新規ユーザーを作成して返す"""
    global _next_user_id
    user = {"id": _next_user_id, "name": name, "email": email}
    _USERS[_next_user_id] = user
    _next_user_id += 1
    return user
