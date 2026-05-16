from tools import bash, read_file, write_file

_TOOLS = {
    "read_file": read_file.run,
    "write_file": write_file.run,
    "bash": bash.run,
}

TOOL_SCHEMAS = [
    read_file.SCHEMA,
    write_file.SCHEMA,
    bash.SCHEMA,
]

def dispatch(name: str, args: dict) -> str:
    if name not in _TOOLS:
        return f"ERROR: unknown tool '{name}'"
    try:
        return _TOOLS[name](**args)
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {e}"