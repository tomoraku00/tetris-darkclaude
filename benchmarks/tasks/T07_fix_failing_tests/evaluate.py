"""T07 評価: pytest 通過数 / 8"""
import subprocess
import sys
from pathlib import Path


def evaluate(workdir: Path, result: dict) -> float:
    date_range_file = workdir / "date_range.py"
    if not date_range_file.exists():
        return 0.0

    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "test_date_range.py", "-v", "--tb=no", "-q"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
            cwd=str(workdir),
        )
    except Exception:
        return 0.0

    passed = 0
    total = 8
    for line in proc.stdout.splitlines():
        if " passed" in line:
            try:
                passed = int(line.strip().split()[0])
            except ValueError:
                pass
    # pytest -q の出力: "4 passed, 4 failed in ..."
    # または "8 passed in ..."
    combined = proc.stdout + proc.stderr
    import re
    m = re.search(r"(\d+) passed", combined)
    if m:
        passed = int(m.group(1))

    return round(passed / total, 3)
