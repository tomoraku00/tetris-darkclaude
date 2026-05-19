"""API テスト"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.api import get_user


def test_get_user_returns_dict():
    result = get_user(1)
    assert isinstance(result, dict)


def test_get_user_has_id():
    result = get_user(42)
    assert result["id"] == 42


def test_get_user_active():
    result = get_user(1)
    assert result["active"] is True
