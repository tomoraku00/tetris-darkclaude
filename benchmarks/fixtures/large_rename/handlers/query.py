"""クエリハンドラ"""
from core.base import DataProvider


class QueryHandler:
    def __init__(self, provider: DataProvider) -> None:
        self._provider = provider

    def handle(self, query: str) -> dict:
        results = self._provider.fetch(query)
        return {
            "query": query,
            "count": len(results),
            "results": results,
            "provider": self._provider.describe(),
        }
