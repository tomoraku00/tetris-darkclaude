"""QueryHandler のテスト"""
from core.base import DataProvider
from handlers.query import QueryHandler


class _MockProvider(DataProvider):
    def fetch(self, query: str) -> list:
        return [{"item": query}]


def test_handle_returns_dict():
    h = QueryHandler(_MockProvider())
    r = h.handle("test")
    assert isinstance(r, dict)


def test_handle_query_field():
    h = QueryHandler(_MockProvider())
    r = h.handle("myquery")
    assert r["query"] == "myquery"


def test_handle_count_matches_results():
    h = QueryHandler(_MockProvider())
    r = h.handle("x")
    assert r["count"] == len(r["results"])


def test_handle_provider_field():
    h = QueryHandler(_MockProvider())
    r = h.handle("q")
    assert "provider" in r


def test_handle_results_not_empty():
    h = QueryHandler(_MockProvider())
    r = h.handle("nonempty")
    assert len(r["results"]) > 0
