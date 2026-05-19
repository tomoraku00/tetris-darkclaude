"""非同期カウンター (race condition あり)"""
import asyncio


class AsyncCounter:
    def __init__(self) -> None:
        self.value = 0
        self.history: list[int] = []

    async def increment(self, delay: float = 0.001) -> None:
        # ⚠ race condition: read → modify → write が atomic でない
        current = self.value
        await asyncio.sleep(delay)
        self.value = current + 1
        self.history.append(self.value)

    async def run_concurrent(self, n: int = 100) -> int:
        tasks = [self.increment() for _ in range(n)]
        await asyncio.gather(*tasks)
        return self.value
