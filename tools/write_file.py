from pathlib import Path

PROJECT_ROOT = Path.cwd().resolve()

SCHEMA = {
    "type": "function",
    "function": {
        "name": "write_file",
        "description": "プロジェクト内のファイルに内容を書き込む。新規ファイル作成、または明示的にファイル全体を置き換える場合にのみ使用すること。既存ファイルの局所編集（関数修正、docstring 追加、数行の変更など）には str_replace を使うこと。親ディレクトリがなければ自動作成。",
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