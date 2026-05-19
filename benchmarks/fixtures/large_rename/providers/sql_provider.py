"""SQL データプロバイダ"""
from core.base import DataProvider
from providers.cache import CacheLayer  # 循環依存ポイント


class SQLProvider(DataProvider):
    def __init__(self, dsn: str) -> None:
        self.dsn = dsn
        self._cache: CacheLayer = CacheLayer()

    def fetch(self, query: str) -> list:
        cached = self._cache.get(query)
        if cached is not None:
            return cached
        result = [{"query": query, "dsn": self.dsn}]
        self._cache.set(query, result)
        return result

    def describe(self) -> str:
        return f"DataProvider: SQLProvider({self.dsn})"
