"""E6: Reflexion — 失敗パターンを .darkclaude/reflexion.md に蓄積し、
次回セッションの system prompt に取り込んで同じ失敗を回避する。
"""
from datetime import datetime
from pathlib import Path


_REFLEXION_PATH = Path(".darkclaude") / "reflexion.md"
_MAX_CHARS = 4000  # system prompt への取り込み上限 (コンテキスト節約)


def load_reflexion(path: Path | None = None) -> str:
    """reflexion.md を読み込む。ファイルがなければ空文字列。

    長すぎる場合は末尾 _MAX_CHARS 文字のみ取り込む (最新記録を優先)。
    """
    p = path or _REFLEXION_PATH
    if not p.exists():
        return ""
    try:
        text = p.read_text(encoding="utf-8").strip()
        if len(text) > _MAX_CHARS:
            text = "...(古い記録は省略)...\n\n" + text[-_MAX_CHARS:]
        return text
    except Exception:
        return ""


def append_reflexion(
    task_summary: str,
    failed_approach: str,
    error: str,
    lesson: str,
    path: Path | None = None,
) -> Path:
    """失敗エントリを reflexion.md に追記。ファイルがなければ新規作成。"""
    p = path or _REFLEXION_PATH
    p.parent.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = (
        f"\n## {timestamp}: {task_summary}\n\n"
        f"**試したアプローチ**: {failed_approach}\n"
        f"**エラー**: {error[:500]}\n"
        f"**教訓**: {lesson}\n\n"
        f"---\n"
    )

    if p.exists():
        existing = p.read_text(encoding="utf-8")
        p.write_text(existing + entry, encoding="utf-8")
    else:
        p.write_text(f"# DarkClaude Reflexion Log\n{entry}", encoding="utf-8")

    return p
