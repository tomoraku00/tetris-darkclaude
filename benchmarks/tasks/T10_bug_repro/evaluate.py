"""T10 評価: テストファイル存在 + depth=1 テスト + 全テスト通過 + バグ修正確認"""
import subprocess
import sys
import re
from pathlib import Path


def evaluate(workdir: Path, result: dict) -> float:
    score = 0.0

    # テストファイルが作成されているか (0.1)
    test_files = list(workdir.glob("test_*.py")) + list(workdir.glob("*_test.py"))
    if not test_files:
        return 0.0
    score += 0.10

    test_file = test_files[0]
    test_src = test_file.read_text(encoding="utf-8")

    # depth=1 のテストケースが含まれているか (0.2)
    if "depth=1" in test_src or "depth = 1" in test_src:
        score += 0.20

    # pytest 全テスト通過 (0.5)
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", test_file.name, "-q", "--tb=no"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            cwd=str(workdir),
        )
        combined = proc.stdout + proc.stderr
        m_passed = re.search(r"(\d+) passed", combined)
        m_failed = re.search(r"(\d+) failed", combined)
        passed = int(m_passed.group(1)) if m_passed else 0
        failed = int(m_failed.group(1)) if m_failed else 0
        if failed == 0 and passed > 0:
            score += 0.50
        elif passed > 0:
            score += 0.25 * min(passed / max(passed + failed, 1), 1.0)
    except Exception:
        pass

    # list_utils.py に "depth - 1" が含まれているか（バグ修正の証拠）(0.2)
    utils_file = workdir / "list_utils.py"
    if utils_file.exists():
        utils_src = utils_file.read_text(encoding="utf-8")
        if "depth - 1" in utils_src or "depth-1" in utils_src:
            score += 0.20

    return min(score, 1.0)
