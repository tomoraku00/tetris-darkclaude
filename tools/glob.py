from pathlib import Path
from typing import Iterator

PROJECT_ROOT = Path.cwd().resolve()

_MAX_RESULTS = 200
_MAX_OUTPUT = 4000

_SKIP_DIRS = {
    ".git", "node_modules", "__pycache__",
    ".venv", "venv", ".mypy_cache", ".pytest_cache",
}

SCHEMA = {
    "type": "function",
    "function": {
        "name": "glob",
        "description": "プロジェクト内のファイルパスを glob パターンで検索し、マッチしたパスのリストを返す。ファイルパスの検索に使う。ファイル内容の検索には grep を使うこと。",
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "glob パターン（例: '**/*.py', 'tools/*.py'）"
                },
                "path": {
                    "type": "string",
                    "description": "検索開始ディレクトリ（省略時は '.'）"
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


def run(pattern: str, path: str = ".") -> str:
    base = (PROJECT_ROOT / path).resolve()
    if not base.is_relative_to(PROJECT_ROOT):
        return f"ERROR: path outside project root: {path}"
    if not base.exists():
        return f"ERROR: path not found: {path}"
    if not base.is_dir():
        return f"ERROR: not a directory: {path}"

    results: list[str] = []
    truncated = False

    for file in _walk(base):
        if file.match(pattern):
            results.append(str(file.relative_to(PROJECT_ROOT)))
            if len(results) >= _MAX_RESULTS:
                truncated = True
                break

    if not results:
        return "(no matches)"

    output = "\n".join(results)
    if truncated:
        output += f"\n... (truncated at {_MAX_RESULTS} results)"
    if len(output) > _MAX_OUTPUT:
        output = output[:_MAX_OUTPUT] + "\n... (output truncated at 4000 chars)"

    return output
