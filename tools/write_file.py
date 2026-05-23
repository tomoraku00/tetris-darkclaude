from pathlib import Path

PROJECT_ROOT = Path.cwd().resolve()

SCHEMA = {
    "type": "function",
    "function": {
        "name": "write_file",
        "description": "Write content to a file in the project. Use for new files or full rewrites only. For partial edits (fix a function, add docstring, multiple changes), use str_replace instead. Creates parent directories automatically.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative path from project root"
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to the file"
                }
            },
            "required": ["path", "content"]
        }
    }
}

def run(path: str, content: str) -> str:
    p = Path(path)
    target = p.resolve() if p.is_absolute() else (PROJECT_ROOT / path).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"OK: wrote {len(content)} chars to {path}"
