"""T03 評価: pytest でリファクタ後の utils.py テストを実行"""
import subprocess
import sys
from pathlib import Path


def evaluate(workdir: Path, result: dict) -> float:
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "test_utils.py", "-q", "--tb=no"],
        capture_output=True,
        text=True,
        cwd=str(workdir),
    )
    # 全テスト通過なら 1.0、1 個も通らなければ 0.0
    output = r.stdout + r.stderr
    # "5 passed" のような表現をパース
    import re
    m = re.search(r"(\d+) passed", output)
    if m:
        passed = int(m.group(1))
        total = 5  # テスト数
        return passed / total
    return 0.0
