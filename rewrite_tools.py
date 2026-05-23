from pathlib import Path

tools_dir = Path(r"C:\Users\tomo_rrow\Documents\nanoclaude\tools")

# read_file.py
(tools_dir / "read_file.py").write_text('''from pathlib import Path
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
''', encoding="utf-8")

# str_replace.py
import difflib as _difflib
(tools_dir / "str_replace.py").write_text('''import difflib
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
        diff_text = "\\n".join(diff_lines[2:])
        return f"Replaced 1 occurrence in {path}\\n[DIFF_START]\\n{diff_text}\\n[DIFF_END]"
    return f"Replaced 1 occurrence in {path}"
''', encoding="utf-8")

# write_file.py
(tools_dir / "write_file.py").write_text('''from pathlib import Path

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
''', encoding="utf-8")

# glob.py - keep existing logic, just fix description
glob_content = (tools_dir / "glob.py").read_text(encoding="utf-8", errors="replace")
# Replace only the SCHEMA description part
import re
new_glob = re.sub(
    r'"description":\s*"[^"]*glob[^"]*"',
    '"description": "Find files matching a glob pattern. Returns matching file paths. Use ** for recursive search."',
    glob_content, count=1
)
(tools_dir / "glob.py").write_text(new_glob, encoding="utf-8")

print("Done: read_file.py, str_replace.py, write_file.py, glob.py rewritten")