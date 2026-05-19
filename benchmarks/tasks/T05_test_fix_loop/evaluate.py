"""T05 評価: pytest で何個のテストが通過したか"""
import subprocess
import sys
import re
from pathlib import Path

_TOTAL_TESTS = 5


def evaluate(workdir: Path, result: dict) -> float:
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "test_calculator.py", "-q", "--tb=no"],
        capture_output=True,
        text=True,
        cwd=str(workdir),
    )
    output = r.stdout + r.stderr
    m = re.search(r"(\d+) passed", output)
    if m:
        return int(m.group(1)) / _TOTAL_TESTS
    return 0.0
