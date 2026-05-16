from tools import bash, glob, grep, read_file, write_file

_TOOLS = {
    "read_file":  read_file.run,
    "write_file": write_file.run,
    "bash":       bash.run,
    "grep":       grep.run,
    "glob":       glob.run,
}

TOOL_SCHEMAS = [
    read_file.SCHEMA,
    write_file.SCHEMA,
    bash.SCHEMA,
    grep.SCHEMA,
    glob.SCHEMA,
]

_PLAN_BLOCKED = {"write_file", "bash"}


def dispatch(name: str, args: dict, plan_mode: bool = False) -> str:
    if plan_mode and name in _PLAN_BLOCKED:
        return (
            f"ERROR: {name} は Plan モード中は使用できません。"
            "/plan で通常モードに戻してください。"
        )
    if name not in _TOOLS:
        return f"ERROR: unknown tool '{name}'"
    try:
        return _TOOLS[name](**args)
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {e}"