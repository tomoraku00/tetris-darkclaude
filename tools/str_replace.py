from pathlib import Path

PROJECT_ROOT = Path.cwd().resolve()

SCHEMA = {
    "type": "function",
    "function": {
        "name": "str_replace",
        "description": (
            "プロジェクト内ファイルの特定文字列を別の文字列に置換する。"
            "局所編集（関数の修正、docstring 追加、数行の変更など）に使用。"
            "ファイル全体の上書きには write_file を使うこと。"
            "old_str は対象ファイル内で正確に 1 回だけ出現する必要があり、"
            "複数箇所に存在する場合はエラーとなる。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "プロジェクトルートからの相対パス",
                },
                "old_str": {
                    "type": "string",
                    "description": (
                        "置換対象の文字列。ファイル中に正確に 1 回だけ出現する必要あり。"
                        "一意性を確保するため、周辺コンテキストを含めること"
                    ),
                },
                "new_str": {
                    "type": "string",
                    "description": "置換後の文字列。空文字列を指定すると old_str を削除",
                },
            },
            "required": ["path", "old_str", "new_str"],
        },
    },
}


def run(path: str, old_str: str, new_str: str) -> str:
    target = (PROJECT_ROOT / path).resolve()
    if not target.is_relative_to(PROJECT_ROOT):
        return f"ERROR: path outside project root: {path}"
    if not target.exists():
        return f"ERROR: file not found: {path}"
    if not target.is_file():
        return f"ERROR: not a file: {path}"
    try:
        content = target.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return f"ERROR: cannot decode as utf-8: {path}"

    count = content.count(old_str)
    if count == 0:
        return f"ERROR: old_str not found in {path}"
    if count > 1:
        return (
            f"ERROR: old_str found {count} times in {path}, must be unique. "
            "Add more surrounding context to make it unique."
        )

    new_content = content.replace(old_str, new_str, 1)
    target.write_text(new_content, encoding="utf-8")
    return f"Replaced 1 occurrence in {path}"
