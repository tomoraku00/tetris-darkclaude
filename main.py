import sys
import json
import subprocess
from pathlib import Path
import ollama
from tools.registry import TOOL_SCHEMAS, dispatch

# Windows cp932 端末でも日本語ツール出力を正しく表示する
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DEFAULT_MODEL = "qwen3:8b"
_CONFIG_PATH = Path(__file__).parent / "config.json"


def load_config() -> dict:
    if _CONFIG_PATH.exists():
        try:
            return json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"model": DEFAULT_MODEL}


def save_config(config: dict) -> None:
    _CONFIG_PATH.write_text(
        json.dumps(config, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def get_installed_models() -> list[str]:
    try:
        resp = ollama.list()
        if hasattr(resp, "models"):
            return [m.model for m in resp.models if m.model]
        return [m.get("model", m.get("name", "")) for m in resp.get("models", [])]
    except Exception:
        return []


_PLAN_SYSTEM_PROMPT = (
    "あなたは現在 Plan モードです。実装は行わず、これから取るべき手順を"
    "箇条書きで提示してください。ファイル書き込み（write_file）や bash 実行"
    "は禁止されています。読み取り系ツール（read_file / grep / glob）のみ"
    "使用可能です。"
)


def chat_turn(messages: list, user_input: str, model: str, plan_mode: bool = False) -> None:
    """Process one user input, including any tool-use loops."""
    messages.append({"role": "user", "content": user_input})

    while True:
        send_messages = messages
        if plan_mode:
            send_messages = [{"role": "system", "content": _PLAN_SYSTEM_PROMPT}] + messages

        response = ollama.chat(
            model=model,
            messages=send_messages,
            tools=TOOL_SCHEMAS,
        )
        msg = response["message"]
        messages.append(msg)

        tool_calls = msg.get("tool_calls")
        if not tool_calls:
            # 通常のテキスト応答 → ターン終了
            print(f"\nDarkClaude: {msg.get('content', '')}\n")
            return

        # ツール呼び出しを順に実行
        for call in tool_calls:
            name = call["function"]["name"]
            args = call["function"]["arguments"]
            preview = str(args)[:80]
            print(f"  [tool] {name}({preview})")
            result = dispatch(name, args, plan_mode=plan_mode)
            shown = result[:100] + ("..." if len(result) > 100 else "")
            print(f"  [result] {shown}")
            messages.append({
                "role": "tool",
                "content": result,
                "name": name,
            })
        # 次のループへ（モデルにツール結果を渡して続きを生成させる）


def main():
    config = load_config()
    model: str = config.get("model", DEFAULT_MODEL)
    messages: list = []
    plan_mode: bool = False

    # ASCII art logo (ASCII characters only, codepage非依存)
    print(r"""
 ____             _     ____ _                _
|  _ \  __ _ _ __| | __/ ___| | __ _ _   _  __| | ___
| | | |/ _` | '__| |/ / |   | |/ _` | | | |/ _` |/ _ \
| |_| | (_| | |  |   <| |___| | (_| | |_| | (_| |  __/
|____/ \__,_|_|  |_|\_\\____|_|\__,_|\__,_|\__,_|\___|
                                             v0.5
""")
    print(f"Model: {model}")
    print("Commands: /exit /quit /bye  |  /models  |  /model <name>  |  /setmodel <name>  |  /plan")
    print()

    try:
        while True:
            prompt = "User [PLAN] > " if plan_mode else "User > "
            user_input = input(prompt).strip()
            if not user_input:
                continue

            # 終了
            if user_input in ["/exit", "/quit", "/bye"]:
                print("Goodbye!")
                break

            # インストール済みモデル一覧
            if user_input == "/models":
                proc = subprocess.run(
                    ["ollama", "list"],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
                print(proc.stdout or proc.stderr or "(no output)")
                continue

            # モデル確認・切り替え
            if user_input == "/model" or user_input.startswith("/model "):
                name = user_input[7:].strip() if user_input.startswith("/model ") else ""
                if not name:
                    print(f"Current model: {model}")
                else:
                    installed = get_installed_models()
                    if name not in installed:
                        print(f"Warning: '{name}' not found.")
                        if installed:
                            print(f"Installed: {', '.join(installed)}")
                    else:
                        model = name
                        print(f"Switched to: {model}")
                continue

            # モデル永続切り替え（config.json に書き込み）
            if user_input == "/setmodel" or user_input.startswith("/setmodel "):
                name = user_input[10:].strip() if user_input.startswith("/setmodel ") else ""
                if not name:
                    print("Usage: /setmodel <name>")
                else:
                    installed = get_installed_models()
                    if name not in installed:
                        print(f"Warning: '{name}' not found. config.json is unchanged.")
                        if installed:
                            print(f"Installed: {', '.join(installed)}")
                    else:
                        model = name
                        save_config({"model": model})
                        print(f"Switched to: {model} (saved to config.json)")
                continue

            # Plan モードトグル
            if user_input == "/plan":
                plan_mode = not plan_mode
                status = "ON" if plan_mode else "OFF"
                print(f"Plan モード: {status}")
                continue

            chat_turn(messages, user_input, model, plan_mode=plan_mode)

    except KeyboardInterrupt:
        print("\nCtrl+C detected. Exiting safely.")


if __name__ == "__main__":
    main()
