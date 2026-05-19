"""T02 評価: py_compile で修正後の bug.py を検証"""
import subprocess
import sys
from pathlib import Path


def evaluate(workdir: Path, result: dict) -> float:
    bug_py = workdir / "bug.py"
    if not bug_py.exists():
        return 0.0
    r = subprocess.run(
        [sys.executable, "-m", "py_compile", str(bug_py)],
        capture_output=True,
    )
    return 1.0 if r.returncode == 0 else 0.0
