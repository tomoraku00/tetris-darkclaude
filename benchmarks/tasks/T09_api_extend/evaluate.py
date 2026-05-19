"""T09 評価: 関数存在 + ハンドラ存在 + 既存テスト + 新テスト + 動作確認"""
import subprocess
import sys
import re
from pathlib import Path


def evaluate(workdir: Path, result: dict) -> float:
    base = workdir / "api_extend"
    if not base.exists():
        return 0.0

    score = 0.0

    # api.py に新関数が存在 (各 0.1)
    api_src = (base / "api.py").read_text(encoding="utf-8") if (base / "api.py").exists() else ""
    if "get_user_posts" in api_src:
        score += 0.10
    if "delete_user" in api_src:
        score += 0.10

    # handlers.py に新ハンドラが存在 (各 0.1)
    handler_src = (base / "handlers.py").read_text(encoding="utf-8") if (base / "handlers.py").exists() else ""
    if "handle_get_user_posts" in handler_src:
        score += 0.10
    if "handle_delete_user" in handler_src:
        score += 0.10

    # pytest 実行（既存 3 件 + 新テスト）
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=no"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
            cwd=str(base),
        )
        combined = proc.stdout + proc.stderr
        m_passed = re.search(r"(\d+) passed", combined)
        m_failed = re.search(r"(\d+) failed", combined)
        passed = int(m_passed.group(1)) if m_passed else 0
        failed = int(m_failed.group(1)) if m_failed else 0
        total = passed + failed

        # 既存 3 件が通過 (0.2)
        if passed >= 3 and failed == 0:
            score += 0.20
        elif passed >= 3:
            score += 0.10

        # 新テスト 3 件以上 (各 1 件 0.067 → 合計 0.20)
        new_tests = max(0, total - 3)
        score += min(new_tests, 3) * (0.20 / 3)

    except Exception:
        pass

    # 動作確認: get_user_posts が正しい結果を返すか (0.20)
    check_script = """
import sys
sys.path.insert(0, ".")
from api import get_user_posts, delete_user
posts = get_user_posts(1)
assert posts is not None and len(posts) == 2, f"Expected 2 posts for user 1, got {posts}"
posts_none = get_user_posts(999)
assert posts_none is None, "Expected None for non-existent user"
ok = delete_user(2)
assert ok is True
from api import get_user
assert get_user(2) is None
print("OK")
"""
    try:
        proc2 = subprocess.run(
            [sys.executable, "-c", check_script],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
            cwd=str(base),
        )
        if "OK" in proc2.stdout:
            score += 0.20
    except Exception:
        pass

    return min(score, 1.0)
