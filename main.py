import collections
import random
import sys
import json
import subprocess
import threading
import time
from pathlib import Path
import ollama
from tools.registry import TOOL_SCHEMAS, dispatch
from tools.approval import request_approval

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


_THINKING_VERBS = [
    "Thinking", "Cooking", "Brewing", "Cogitating",
    "Crunching", "Pondering", "Simmering",
    "思考中", "考え中", "推論中", "解析中", "演算中", "思索中", "分析中",
]

_CLEAR_LINE = "\r" + " " * 60 + "\r"


class ThinkingIndicator:
    """ollama.chat() 中に '✻ <verb> for Ns' を 1 秒ごとに上書き表示するコンテキストマネージャ。"""

    def __init__(self) -> None:
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._verb = ""

    def _run(self) -> None:
        start = time.monotonic()
        while not self._stop.wait(1.0):
            elapsed = time.monotonic() - start
            print(f"\r✻ {self._verb} for {elapsed:.0f}s", end="", flush=True)

    def __enter__(self) -> "ThinkingIndicator":
        self._verb = random.choice(_THINKING_VERBS)
        self._stop.clear()
        print(f"✻ {self._verb} for 0s", end="", flush=True)
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *_) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)
        print(_CLEAR_LINE, end="", flush=True)


_PLAN_SYSTEM_PROMPT = (
    "あなたは現在 Plan モードです。実装は行わず、これから取るべき手順を"
    "箇条書きで提示してください。ファイル書き込み（write_file）や bash 実行"
    "は禁止されています。読み取り系ツール（read_file / grep / glob）のみ"
    "使用可能です。"
)


def chat_turn(
    messages: list,
    user_input: str,
    model: str,
    plan_mode: bool = False,
    allowed_write_paths: set[str] | None = None,
    allowed_bash_commands: set[str] | None = None,
) -> None:
    """Process one user input, including any tool-use loops."""
    messages.append({"role": "user", "content": user_input})

    if allowed_write_paths is None:
        allowed_write_paths = set()
    if allowed_bash_commands is None:
        allowed_bash_commands = set()

    call_count = 0
    recent_calls: collections.deque = collections.deque(maxlen=3)
    turn_start = time.monotonic()

    while True:
        send_messages = messages
        if plan_mode:
            send_messages = [{"role": "system", "content": _PLAN_SYSTEM_PROMPT}] + messages

        with ThinkingIndicator():
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
            print(f"  (合計 {time.monotonic() - turn_start:.1f}s)")
            return

        # ツール呼び出しを順に実行
        limit_reached = False
        for call in tool_calls:
            name = call["function"]["name"]
            args = call["function"]["arguments"]

            # ② ターン内総呼び出し上限（25回）
            call_count += 1
            if call_count > 25:
                error = (
                    "ERROR: このターンの tool_call 回数が上限（25回）に達しました。"
                    "タスクを分割するか、再度指示してください。"
                )
                print(f"  [tool] {name}(...) → 上限到達でブロック")
                messages.append({"role": "tool", "content": error, "name": name})
                limit_reached = True
                break

            # ① 同一呼び出し連続検出（直前 3 回が同一なら 4 回目以降をブロック）
            call_key = (name, json.dumps(args, sort_keys=True, ensure_ascii=False))
            if len(recent_calls) == 3 and all(k == call_key for k in recent_calls):
                error = (
                    "ERROR: 同じツール呼び出しが3回繰り返されました。"
                    "引数を変えるか、別のアプローチを試してください。"
                )
                print(f"  [tool] {name}(...) → 連続同一呼び出しでブロック")
                messages.append({"role": "tool", "content": error, "name": name})
                recent_calls.append(call_key)
                continue
            recent_calls.append(call_key)

            # 承認ゲート（Plan モード OFF かつ副作用ツールのみ）
            if not plan_mode and name in ("write_file", "bash"):
                if name == "write_file":
                    key = args.get("path", "")
                    allowed_set = allowed_write_paths
                else:
                    key = args.get("command", "").strip()
                    allowed_set = allowed_bash_commands

                if not key:
                    preview = str(args)[:80]
                    print(f"  [tool] {name}({preview}) -> denied (invalid args)")
                    messages.append({"role": "tool", "content": "ERROR: ユーザーが承認を拒否しました", "name": name})
                    continue

                if key not in allowed_set:
                    decision = request_approval(name, args)
                    if decision == "always_allow":
                        allowed_set.add(key)
                    elif decision == "deny":
                        preview = str(args)[:80]
                        print(f"  [tool] {name}({preview}) -> denied by user")
                        messages.append({"role": "tool", "content": "ERROR: ユーザーが承認を拒否しました", "name": name})
                        continue

            tool_start = time.monotonic()
            result = dispatch(name, args, plan_mode=plan_mode)
            tool_elapsed = time.monotonic() - tool_start

            preview = str(args)[:80]
            print(f"  [tool] {name}({preview}) [{tool_elapsed:.1f}s]")
            shown = result[:100] + ("..." if len(result) > 100 else "")
            print(f"  [result] {shown}")
            messages.append({
                "role": "tool",
                "content": result,
                "name": name,
            })

        if limit_reached:
            print("\n[安全機構] ターン内 tool_call 上限（25回）に達しました。処理を中断します。\n")
            return
        # 次のループへ（モデルにツール結果を渡して続きを生成させる）


def main():
    config = load_config()
    model: str = config.get("model", DEFAULT_MODEL)
    messages: list = []
    plan_mode: bool = False
    allowed_write_paths: set[str] = set()
    allowed_bash_commands: set[str] = set()

    # ASCII art logo (ASCII characters only, codepage非依存)
    print(r"""
 ____             _     ____ _                _
|  _ \  __ _ _ __| | __/ ___| | __ _ _   _  __| | ___
| | | |/ _` | '__| |/ / |   | |/ _` | | | |/ _` |/ _ \
| |_| | (_| | |  |   <| |___| | (_| | |_| | (_| |  __/
|____/ \__,_|_|  |_|\_\\____|_|\__,_|\__,_|\__,_|\___|
                                             v0.6.1
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

            chat_turn(
                messages, user_input, model,
                plan_mode=plan_mode,
                allowed_write_paths=allowed_write_paths,
                allowed_bash_commands=allowed_bash_commands,
            )

    except KeyboardInterrupt:
        print("\nCtrl+C detected. Exiting safely.")


if __name__ == "__main__":
    main()
