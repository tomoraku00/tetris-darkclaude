"""T08 評価: 正確性 (0.4) + set 使用 (0.2) + パフォーマンス (0.4)"""
import subprocess
import sys
import time
from pathlib import Path


def evaluate(workdir: Path, result: dict) -> float:
    finder_file = workdir / "finder.py"
    if not finder_file.exists():
        return 0.0

    score = 0.0
    finder_src = finder_file.read_text(encoding="utf-8")

    # 正確性: pytest 通過 (0.4)
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "test_finder.py", "-q", "--tb=no"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            cwd=str(workdir),
        )
        import re
        m = re.search(r"(\d+) passed", proc.stdout + proc.stderr)
        if m:
            passed = int(m.group(1))
            score += 0.4 * min(passed / 7, 1.0)
    except Exception:
        pass

    # set / dict 使用（O(n) 改善の証拠）(0.2)
    if "set(" in finder_src or "= {}" in finder_src or "dict(" in finder_src:
        score += 0.2

    # パフォーマンス: n=2500 で 0.5 秒以内 (0.4)
    perf_script = """
import time, sys
sys.path.insert(0, ".")
from finder import find_duplicates, find_common_elements, count_unique
import random
random.seed(42)
n = 2500
data = [random.randint(0, n // 2) for _ in range(n)]
data_b = [random.randint(0, n // 2) for _ in range(n)]
t0 = time.perf_counter()
find_duplicates(data)
find_common_elements(data, data_b)
count_unique(data)
t1 = time.perf_counter()
print(f"{t1 - t0:.4f}")
"""
    try:
        proc2 = subprocess.run(
            [sys.executable, "-c", perf_script],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            cwd=str(workdir),
        )
        elapsed = float(proc2.stdout.strip())
        if elapsed < 0.5:
            score += 0.4
        elif elapsed < 2.0:
            score += 0.2
    except Exception:
        pass

    return min(score, 1.0)
