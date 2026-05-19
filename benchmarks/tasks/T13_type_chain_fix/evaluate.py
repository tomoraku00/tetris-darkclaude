"""T13 評価: mypy strict 通過 (0.5) + pytest 通過 (0.3) + Any 不使用 (0.2)"""
import subprocess
import sys
import re
from pathlib import Path


def evaluate(workdir: Path, result: dict) -> float:
    score = 0.0
    shapes_file = workdir / "shapes.py"
    if not shapes_file.exists():
        return 0.0

    src = shapes_file.read_text(encoding="utf-8", errors="replace")

    # 1. mypy --strict 通過 (0.5)
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "mypy", "--strict", "shapes.py"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            cwd=str(workdir),
        )
        error_count = sum(1 for line in proc.stdout.splitlines() if ": error:" in line)
        if error_count == 0:
            score += 0.50
        elif error_count <= 5:
            score += 0.30
        elif error_count <= 15:
            score += 0.15
    except Exception:
        pass

    # 2. pytest 通過 (0.3): 全 8 テスト
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "test_shapes.py", "-q", "--tb=no"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            cwd=str(workdir),
        )
        m = re.search(r"(\d+) passed", proc.stdout + proc.stderr)
        if m:
            passed = int(m.group(1))
            score += 0.30 * min(passed / 8, 1.0)
    except Exception:
        pass

    # 3. Any 不使用 (0.2)
    # "Any" が型注釈として使われていないか（any() 組み込みは除外）
    has_any_annotation = any(
        "Any" in line and not line.strip().startswith("#")
        for line in src.splitlines()
        if re.search(r":\s*Any|->.*Any|\bAny\b", line)
    )
    if not has_any_annotation:
        score += 0.20

    return min(score, 1.0)
