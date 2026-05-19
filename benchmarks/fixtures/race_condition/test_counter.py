"""カウンターが 100 並列実行後に正確に 100 になるか"""
import asyncio
from counter import AsyncCounter


def test_concurrent_correctness():
    """20 回連続で 100 並列実行し、毎回 value == 100 であること"""
    for _ in range(20):
        c = AsyncCounter()
        result = asyncio.run(c.run_concurrent(100))
        assert result == 100, f"Expected 100, got {result}"
