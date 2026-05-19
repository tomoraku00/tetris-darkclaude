"""SQLProvider + CacheLayer のテスト (循環依存があると import 失敗)"""
from core.base import DataProvider
from providers.sql_provider import SQLProvider
from providers.cache import CacheLayer


def test_sql_provider_is_data_provider():
    p = SQLProvider("db://test")
    assert isinstance(p, DataProvider)


def test_sql_provider_fetch_returns_list():
    p = SQLProvider("db://test")
    assert isinstance(p.fetch("select 1"), list)


def test_sql_provider_cache_hit():
    p = SQLProvider("db://test")
    r1 = p.fetch("q")
    r2 = p.fetch("q")
    assert r1 is r2


def test_cache_layer_set_get():
    c = CacheLayer()
    c.set("key", [1, 2, 3])
    assert c.get("key") == [1, 2, 3]


def test_cache_layer_clear():
    c = CacheLayer()
    c.set("key", [42])
    c.clear()
    assert c.get("key") is None
