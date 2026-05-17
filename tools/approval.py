import sys


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
        always_label = f"Always allow writes to '{path}'"
    elif tool_name == "bash":
        command = args.get("command", "").strip()
        print(f"    Command: {command}")
        always_label = f"Always allow '{command}'"
    else:
        always_label = f"Always allow {tool_name}"

    print()
    print("    1. Allow once")
    print(f"    2. {always_label}")
    print("    3. Deny")

    while True:
        try:
            choice = input("  Choice [1-3]: ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            return "deny"

        if choice == "1":
            return "allow_once"
        elif choice == "2":
            return "always_allow"
        elif choice == "3":
            return "deny"
