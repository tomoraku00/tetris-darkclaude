"""ミドルウェア基底"""
from providers.sql_provider import SQLProvider  # 循環依存ポイント


class MiddlewareBase:
    """ミドルウェアの基底クラス"""

    def __init__(self) -> None:
        self._provider: SQLProvider | None = None

    def set_provider(self, provider: SQLProvider) -> None:
        self._provider = provider

    def execute(self, query: str) -> list:
        if self._provider is None:
            return []
        return self._provider.fetch(query)
