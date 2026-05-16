import re
from pathlib import Path
from typing import Iterator

PROJECT_ROOT = Path.cwd().resolve()

_MAX_MATCHES = 100
_MAX_LINE = 200
_MAX_OUTPUT = 4000

_SKIP_DIRS = {
    ".git", "node_modules", "__pycache__",
    ".venv", "venv", ".mypy_cache", ".pytest_cache",
}

SCHEMA = {
    "type": "function",
    "function": {
        "name": "grep",
        "description": "プロジェクト内のファイルを正規表現で検索し、マッチした行を返す。",
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "検索する正規表現"
                },
                "path": {
                    "type": "string",
                    "description": "検索開始ディレクトリ（省略時は '.'）"
                },
                "include": {
                    "type": "string",
                    "description": "ファイルを絞り込む glob パターン（例: '**/*.py'）"
                },
                "case_insensitive": {
                    "type": "boolean",
                    "description": "大文字小文字を無視する（省略時は false）"
                },
            },
            "required": ["pattern"],
        },
    },
}


def _walk(base: Path) -> Iterator[Path]:
    """除外ディレクトリ・隠しディレクトリをスキップしてファイルを列挙する。"""
    try:
        entries = sorted(base.iterdir())
    except PermissionError:
        return
    for p in entries:
        if p.is_dir():
            if p.name in _SKIP_DIRS or p.name.startswith("."):
                continue
            yield from _walk(p)
        elif p.is_file():
            yield p


def _rglob_filtered(base: Path, pattern: str) -> Iterator[Path]:
    """rglob でパターン絞り込みしつつ除外ディレクトリ・隠しディレクトリをスキップする。"""
    for file in base.rglob(pattern):
        if not file.is_file():
            continue
        parts = file.relative_to(base).parts[:-1]
        if any(part in _SKIP_DIRS or part.startswith(".") for part in parts):
            continue
        yield file


def _is_binary(path: Path) -> bool:
    try:
        return b"\x00" in path.read_bytes()[:1024]
    except Exception:
        return True


def run(
    pattern: str,
    path: str = ".",
    include: str | None = None,
    case_insensitive: bool = False,
) -> str:
    base = (PROJECT_ROOT / path).resolve()
    if not base.is_relative_to(PROJECT_ROOT):
        return f"ERROR: path outside project root: {path}"
    if not base.exists():
        return f"ERROR: path not found: {path}"
    if not base.is_dir():
        return f"ERROR: not a directory: {path}"

    try:
        flags = re.IGNORECASE if case_insensitive else 0
        regex = re.compile(pattern, flags)
    except re.error as e:
        return f"ERROR: invalid regex: {e}"

    matches: list[str] = []
    truncated = False

    files = _rglob_filtered(base, include) if include else _walk(base)
    for file in files:
        if _is_binary(file):
            continue
        try:
            text = file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        rel = file.relative_to(PROJECT_ROOT)
        for lineno, line in enumerate(text.splitlines(), 1):
            if regex.search(line):
                matches.append(f"{rel}:{lineno}:{line[:_MAX_LINE]}")
                if len(matches) >= _MAX_MATCHES:
                    truncated = True
                    break
        if truncated:
            break

    if not matches:
        return "(no matches)"

    result = "\n".join(matches)
    if truncated:
        result += f"\n... (truncated at {_MAX_MATCHES} matches)"
    if len(result) > _MAX_OUTPUT:
        result = result[:_MAX_OUTPUT] + "\n... (output truncated at 4000 chars)"

    return result
