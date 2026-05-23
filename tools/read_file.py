from pathlib import Path
from tools import PROJECT_ROOT

SCHEMA = {
    "type": "function",
    "function": {
        "name": "read_file",
        "description": "Read a file and return its content. Accepts absolute path (C:/dev/...) or relative path (src/main.py).",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute path (e.g. C:/dev/src/main.py) or relative path from project root (e.g. src/main.py)"
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
