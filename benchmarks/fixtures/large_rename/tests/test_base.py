"""DataProvider (→ DataSource) 基底クラスのテスト"""
import pytest
from core.base import DataProvider


class _Concrete(DataProvider):
    def fetch(self, query: str) -> list:
        return [f"result:{query}"]


def test_abstract_cannot_instantiate():
    with pytest.raises(TypeError):
        DataProvider()  # type: ignore


def test_fetch_returns_list():
    p = _Concrete()
    assert isinstance(p.fetch("q"), list)


def test_describe_contains_class_name():
    p = _Concrete()
    assert "Concrete" in p.describe()


def test_fetch_result_content():
    p = _Concrete()
    assert p.fetch("hello") == ["result:hello"]


def test_multiple_queries_differ():
    p = _Concrete()
    assert p.fetch("a") != p.fetch("b")
