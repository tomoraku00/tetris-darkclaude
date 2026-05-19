"""T12 評価: テスト通過 (0.5) + Lock/Queue 使用 (0.3) + インターフェース維持 (0.2)"""
import ast
import subprocess
import sys
import re
from pathlib import Path


def evaluate(workdir: Path, result: dict) -> float:
    score = 0.0
    counter_file = workdir / "counter.py"
    if not counter_file.exists():
        return 0.0

    src = counter_file.read_text(encoding="utf-8", errors="replace")

    # 1. テスト通過 (0.5)
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "test_counter.py", "-q", "--tb=no"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
            cwd=str(workdir),
        )
        m = re.search(r"(\d+) passed", proc.stdout + proc.stderr)
        if m and int(m.group(1)) >= 1:
            score += 0.50
    except Exception:
        pass

    # 2. asyncio.Lock / Queue / Semaphore 使用 (0.3)
    if "asyncio.Lock" in src or "asyncio.Queue" in src or "asyncio.Semaphore" in src:
        score += 0.30

    # 3. インターフェース維持 (0.2)
    try:
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "AsyncCounter":
                methods = [
                    m.name for m in node.body
                    if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))
                ]
                if "increment" in methods and "run_concurrent" in methods:
                    score += 0.20
                break
    except Exception:
        pass

    return min(score, 1.0)
