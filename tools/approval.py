import sys
import questionary


def request_approval(tool_name: str, args: dict) -> str:
    """ツール実行前に承認を求める。戻り値は 'allow_once' / 'always_allow' / 'deny'。"""

    # ✻ アニメが残っている場合に備えて行をクリア
    sys.stdout.write("\r" + " " * 60 + "\r")
    sys.stdout.flush()

    print("  [approval needed]")
    print(f"    Tool: {tool_name}")

    if tool_name == "write_file":
        path = args.get("path", "")
        content = args.get("content", "")
        preview = content.replace("\n", "\\n")
        if len(preview) > 80:
            preview = preview[:80] + "..."
        size = len(content.encode("utf-8"))
        print(f"    Path: {path}")
        print(f"    Content: {preview}")
        print(f"    Size: {size} bytes")
        choices = [
            "Allow once",
            f"Always allow writes to '{path}'",
            "Deny",
        ]
    elif tool_name == "str_replace":
        path = args.get("path", "")
        old_str = args.get("old_str", "")
        new_str = args.get("new_str", "")

        def _trunc(s: str, limit: int = 500) -> str:
            if len(s) > limit:
                return s[:limit] + f"...省略 ({len(s)} chars)"
            return s

        print(f"    Path: {path}")
        print(f"    old_str: {_trunc(old_str)}")
        print(f"    new_str: {_trunc(new_str)}")
        choices = [
            "Allow once",
            f"Always allow writes to '{path}'",
            "Deny",
        ]
    elif tool_name == "bash":
        command = args.get("command", "").strip()
        print(f"    Command: {command}")
        choices = [
            "Allow once",
            f"Always allow '{command}'",
            "Deny",
        ]
    else:
        choices = ["Allow once", f"Always allow {tool_name}", "Deny"]

    try:
        result = questionary.select("Choose:", choices=choices).ask()
    except (KeyboardInterrupt, EOFError):
        print()
        return "deny"

    if result is None:
        return "deny"
    elif result == "Allow once":
        return "allow_once"
    elif result == "Deny":
        return "deny"
    else:
        return "always_allow"
