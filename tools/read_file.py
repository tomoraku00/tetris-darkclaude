from pathlib import Path

PROJECT_ROOT = Path.cwd().resolve()

SCHEMA = {
    "type": "function",
    "function": {
        "name": "read_file",
        "description": "プロジェクト内のファイルを読み込み、内容を文字列で返す。",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "プロジェクトルートからの相対パス（例: 'main.py'）"
                }
            },
            "required": ["path"]
        }
    }
}

def run(path: str) -> str:
    target = (PROJECT_ROOT / path).resolve()
    if not target.is_relative_to(PROJECT_ROOT):
        return f"ERROR: path outside project root: {path}"
    if not target.exists():
        return f"ERROR: file not found: {path}"
    if not target.is_file():
        return f"ERROR: not a file: {path}"
    try:
        return target.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return f"ERROR: cannot decode as utf-8: {path}"