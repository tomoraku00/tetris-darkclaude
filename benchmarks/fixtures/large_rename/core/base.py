"""データ取得の基底クラス"""
from abc import ABC, abstractmethod


class DataProvider(ABC):
    """データ取得の抽象基底"""

    @abstractmethod
    def fetch(self, query: str) -> list:
        pass

    def describe(self) -> str:
        return f"DataProvider: {self.__class__.__name__}"
