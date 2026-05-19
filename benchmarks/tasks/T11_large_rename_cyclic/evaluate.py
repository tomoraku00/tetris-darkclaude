"""T11 評価: rename 整合性 (0.3) + テスト通過 (0.4) + 循環依存解消 (0.3)"""
import subprocess
import sys
import re
from pathlib import Path


def evaluate(workdir: Path, result: dict) -> float:
    score = 0.0

    # 1. DataProvider が非コメント行に残っていないか (0.3)
    remaining = 0
    for py_file in workdir.rglob("*.py"):
        text = py_file.read_text(encoding="utf-8", errors="replace")
        for line in text.splitlines():
            if line.strip().startswith("#"):
                continue
            if "DataProvider" in line:
                remaining += 1

    if remaining == 0:
        score += 0.30
    elif remaining <= 2:
        score += 0.15

    # 2. pytest 通過 (0.4): 全 15 テスト
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=no"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
            cwd=str(workdir),
        )
        m = re.search(r"(\d+) passed", proc.stdout + proc.stderr)
        if m:
            passed = int(m.group(1))
            score += 0.40 * min(passed / 15, 1.0)
    except Exception:
        pass

    # 3. 循環依存解消 (0.3)
    try:
        proc = subprocess.run(
            [sys.executable, "-c",
             "import sys; sys.path.insert(0, '.'); import providers"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            cwd=str(workdir),
        )
        if proc.returncode == 0:
            score += 0.30
    except Exception:
        pass

    return min(score, 1.0)
