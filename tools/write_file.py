from pathlib import Path

PROJECT_ROOT = Path.cwd().resolve()

SCHEMA = {
    "type": "function",
    "function": {
        "name": "write_file",
        "description": "プロジェクト内のファイルに内容を書き込む。既存ファイルは上書き。親ディレクトリがなければ自動作成。",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "プロジェクトルートからの相対パス"
                },
                "content": {
                    "type": "string",
                    "description": "書き込む文字列"
                }
            },
            "required": ["path", "content"]
        }
    }
}

def run(path: str, content: str) -> str:
    target = (PROJECT_ROOT / path).resolve()
    if not target.is_relative_to(PROJECT_ROOT):
        return f"ERROR: path outside project root: {path}"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"OK: wrote {len(content)} chars to {path}"