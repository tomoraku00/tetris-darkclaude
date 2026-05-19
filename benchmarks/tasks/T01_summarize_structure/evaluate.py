"""T01 評価: 応答にキーワードが含まれるか検査"""
from pathlib import Path

_KEYWORDS = ["main.py", "tui", "clients", "tools", "prompts"]


def evaluate(workdir: Path, result: dict) -> float:
    output = result.get("output", "").lower()
    found = sum(1 for kw in _KEYWORDS if kw.lower() in output)
    return found / len(_KEYWORDS)
