"""パフォーマンス計測スクリプト"""
import time
import random
from finder import find_duplicates, find_common_elements, count_unique


def run_benchmark(n: int = 2500) -> dict:
    data = [random.randint(0, n // 2) for _ in range(n)]
    data_b = [random.randint(0, n // 2) for _ in range(n)]

    t0 = time.perf_counter()
    find_duplicates(data)
    t1 = time.perf_counter()
    find_common_elements(data, data_b)
    t2 = time.perf_counter()
    count_unique(data)
    t3 = time.perf_counter()

    return {
        "n": n,
        "find_duplicates_sec": round(t1 - t0, 4),
        "find_common_sec": round(t2 - t1, 4),
        "count_unique_sec": round(t3 - t2, 4),
        "total_sec": round(t3 - t0, 4),
    }


if __name__ == "__main__":
    result = run_benchmark()
    for k, v in result.items():
        print(f"  {k}: {v}")
