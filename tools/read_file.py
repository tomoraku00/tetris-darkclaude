from pathlib import Path
PROJECT_ROOT = Path.cwd().resolve()
SCHEMA = {
    "type": "function",
    "function": {
        "name": "read_file",
        "description": "ファイルを読み込み内容を返す。絶対パス(C:/dev/...)または相対パス(src/main.py)どちらも使用可。",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "絶対パス(例: C:/dev/src/main.py)またはプロジェクトルートからの相対パス(例: src/main.py)"
                }
            },
            "required": ["path"]
        }
    }
}
def run(path: str) -> str:
    p = Path(path)
    target = p.resolve() if p.is_absolute() else (PROJECT_ROOT / path).resolve()
    if not target.exists():
        return f"ERROR: file not found: {path}"
    if not target.is_file():
        return f"ERROR: not a file: {path}"
    try:
        return target.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return target.read_text(encoding="utf-8-sig")
