"""キャッシュレイヤー"""
from core.middleware import MiddlewareBase  # 循環依存ポイント


class CacheLayer(MiddlewareBase):
    def __init__(self) -> None:
        self._store: dict = {}

    def get(self, key: str) -> list | None:
        return self._store.get(key)

    def set(self, key: str, value: list) -> None:
        self._store[key] = value

    def clear(self) -> None:
        self._store.clear()
