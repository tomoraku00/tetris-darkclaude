"""T04 評価: fetch_user への置き換えと pytest 通過を確認"""
import subprocess
import sys
from pathlib import Path

_CHECKS = 4  # 合計チェック数


def evaluate(workdir: Path, result: dict) -> float:
    score = 0

    api_py = (workdir / "src" / "api.py").read_text(encoding="utf-8", errors="replace")
    handlers_py = (workdir / "src" / "handlers.py").read_text(encoding="utf-8", errors="replace")
    test_py = (workdir / "tests" / "test_api.py").read_text(encoding="utf-8", errors="replace")

    # 1. api.py に fetch_user 定義あり
    if "def fetch_user" in api_py:
        score += 1
    # 2. api.py に get_user 定義なし
    if "def get_user" not in api_py:
        score += 1
    # 3. handlers.py が fetch_user を使っている
    if "fetch_user" in handlers_py:
        score += 1
    # 4. pytest 通過
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_api.py", "-q", "--tb=no"],
        capture_output=True,
        text=True,
        cwd=str(workdir),
    )
    if r.returncode == 0:
        score += 1

    return score / _CHECKS
