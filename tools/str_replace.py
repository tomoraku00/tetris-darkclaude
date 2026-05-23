import difflib
from pathlib import Path
from tools import PROJECT_ROOT

SCHEMA = {
    "type": "function",
    "function": {
        "name": "str_replace",
        "description": "Replace a unique string in a file with new text. Use for partial edits (fix a function, add docstring, multiple changes). Use write_file for full rewrites. old_str must appear exactly once in the file.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative path from project root"
                },
                "old_str": {
                    "type": "string",
                    "description": "String to replace. Must appear exactly once. Include surrounding context to ensure uniqueness."
                },
                "new_str": {
                    "type": "string",
                    "description": "Replacement text. Empty string deletes old_str."
                }
            },
            "required": ["path", "old_str", "new_str"]
        }
    }
}

def run(path: str, old_str: str, new_str: str) -> str:
    p = Path(path)
    target = p.resolve() if p.is_absolute() else (PROJECT_ROOT / path).resolve()
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
    diff_lines = list(difflib.unified_diff(
        old_str.splitlines(keepends=True),
        new_str.splitlines(keepends=True),
        lineterm=""
    ))
    if diff_lines:
        diff_text = "\n".join(diff_lines[2:])
        return f"Replaced 1 occurrence in {path}\n[DIFF_START]\n{diff_text}\n[DIFF_END]"
    return f"Replaced 1 occurrence in {path}"
