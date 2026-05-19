"""既存 API テスト"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import api
import handlers


@pytest.fixture(autouse=True)
def reset_state():
    """各テスト前後に API 状態をリセット"""
    api._USERS.clear()
    api._USERS.update({
        1: {"id": 1, "name": "Alice", "email": "alice@example.com"},
        2: {"id": 2, "name": "Bob", "email": "bob@example.com"},
        3: {"id": 3, "name": "Carol", "email": "carol@example.com"},
    })
    api._POSTS.clear()
    api._POSTS.update({
        101: {"id": 101, "user_id": 1, "title": "Hello World", "body": "My first post"},
        102: {"id": 102, "user_id": 1, "title": "Python Tips", "body": "Use list comprehensions"},
        103: {"id": 103, "user_id": 2, "title": "Bob's Post", "body": "Hello from Bob"},
        104: {"id": 104, "user_id": 3, "title": "Carol writes", "body": "Carol here"},
    })
    api._next_user_id = 4
    api._next_post_id = 105
    yield


def test_get_user_found():
    r = handlers.handle_get_user(1)
    assert r["status"] == 200
    assert r["data"]["name"] == "Alice"


def test_get_user_not_found():
    r = handlers.handle_get_user(999)
    assert r["status"] == 404


def test_list_users():
    r = handlers.handle_list_users()
    assert r["status"] == 200
    assert len(r["data"]) == 3
