import collections
import random
import sys
import json
import subprocess
import threading
import time
from pathlib import Path
from clients import get_client
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.key_binding import KeyBindings
from tools.registry import TOOL_SCHEMAS, dispatch
from tools.approval import request_approval
from session_log import SessionLog

# Windows cp932 端末でも日本語ツール出力を正しく表示する
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DEFAULT_MODEL = "qwen3:8b"
FALLBACK_MODEL = "qwen3:8b"
DEFAULT_THINK_MODE = "show"
THINK_MODES = ("show", "hide", "off")
_CONFIG_PATH = Path(__file__).parent / "config.json"
DEFAULT_LOGGING_ENABLED = True


def load_config() -> dict:
    if _CONFIG_PATH.exists():
        try:
            return json.loads(_CONFIG_PATH.read_text(encoding="utf-8-sig"))
        except Exception:
            pass
    return {"model": DEFAULT_MODEL}


def save_config(config: dict) -> None:
    _CONFIG_PATH.write_text(
        json.dumps(config, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _to_dict(obj) -> dict:
    """Ollama レスポンスオブジェクトを dict 化する（JSON 直列化のため）。"""
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "dict"):
        return obj.dict()
    try:
        return vars(obj)
    except TypeError:
        return {"raw_repr": str(obj)}


def get_installed_models(client) -> list[str]:
    return client.list_models()


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


class ThinkStripper:
    """Strip <think>...</think> blocks from a stream of text chunks."""

    def __init__(self) -> None:
        self.in_think = False
        self.buffer = ""

    def feed(self, chunk: str) -> str:
        self.buffer += chunk
        out: list[str] = []
        while self.buffer:
            if self.in_think:
                end = self.buffer.find("</think>")
                if end == -1:
                    keep = min(len(self.buffer), 7)
                    self.buffer = self.buffer[-keep:] if keep else ""
                    return "".join(out)
                self.buffer = self.buffer[end + len("</think>"):]
                self.in_think = False
            else:
                start = self.buffer.find("<think>")
                if start == -1:
                    keep = min(len(self.buffer), 6)
                    out.append(self.buffer[:-keep] if keep else self.buffer)
                    self.buffer = self.buffer[-keep:] if keep else ""
                    return "".join(out)
                out.append(self.buffer[:start])
                self.buffer = self.buffer[start + len("<think>"):]
                self.in_think = True
        return "".join(out)

    def flush(self) -> str:
        if self.in_think:
            return ""
        out = self.buffer
        self.buffer = ""
        return out


_PLAN_SYSTEM_PROMPT = (
    "あなたは現在 Plan モードです。実装は行わず、これから取るべき手順を"
    "箇条書きで提示してください。ファイル書き込み（write_file）や bash 実行"
    "は禁止されています。読み取り系ツール（read_file / grep / glob）のみ"
    "使用可能です。"
)

_SYSTEM_PROMPT = (
    "## あなたの役割\n\n"
    "あなたは DarkClaude です。ローカルで動く Qwen3 ベースの\n"
    "コーディングエージェントで、プロジェクト内のコード読解・編集・\n"
    "シェルコマンド実行を通じてユーザーを補佐します。\n"
    "作業対象は常に Windows 上のローカルプロジェクトです。\n\n"
    "## 振る舞い指針\n\n"
    "### 応答言語\n\n"
    "ユーザーが日本語で質問した場合は日本語で、英語の場合は英語で応答すること。\n"
    "ユーザーの使用言語と異なる言語で応答してはならない。\n\n"
    "### 応答スタイル\n\n"
    "応答は技術文書として読みやすい文体で書くこと。絵文字、過剰な装飾、\n"
    'マーケティング調の表現（"🌟", "Pro Tip", "Final Note",\n'
    '"**Key Features**" のような見出し装飾、感嘆符の多用）は使わない。\n'
    "箇条書きは要素が 3 つ以上ある時のみ使い、それ未満なら散文で書く。\n\n"
    "### プロジェクト固有名詞の取り扱い\n\n"
    "プロジェクトのファイル名、関数名、コマンド、設定項目等の固有名詞は、\n"
    "実ファイル（read_file / grep / glob で確認したもの）または前のターンで\n"
    "ユーザーが明示したものだけを使用すること。\n"
    "未確認の名詞を「もっともらしい推測」で生成してはならない。\n"
    "不明な場合は、その旨を明示するか、ツール呼び出しで確認してから応答すること。\n\n"
    "### ツール結果の参照\n\n"
    "ツール呼び出しの結果は必ず応答に反映すること。\n"
    "ツール結果を取得した後に、結果と無関係な汎用的な説明・分析・推奨に\n"
    "流れてはならない。\n\n"
    "ユーザーが「X を Y して」と依頼した場合、X に関する一般的解説ではなく\n"
    "Y を実行することを優先する。「ファイル編集」「ツール実行」が主旨であれば、\n"
    "まずツールを呼び出し、その後に必要最小限の説明を加える。\n\n"
    "### 空のツール結果の扱い\n\n"
    'ツールが空の出力（"" や "(no output)"）を返した場合、それは正常な結果である\n'
    "可能性が高い。「曖昧な結果」として複数の可能性を列挙する反応は避けること。\n"
    "ツール定義に従って、空出力は「正常終了かつ出力なし」と解釈すること。\n"
    "（例: Start-Sleep、mkdir、rm 等は出力なしで成功する）\n\n"
    "## ツール呼び出しのプロトコル\n\n"
    "ツール呼び出しは必ず tool_calls フィールドで行うこと。\n"
    "message content に JSON 形式のツール呼び出しテキストを出力しては\n"
    "ならない（実ツール呼び出しが発火せず、ユーザーは混乱する）。\n\n"
    "ツールを呼び出すべきタイミングでは、応答テキストを返すのではなく\n"
    "必ずツールを呼び出すこと。\n\n"
    "## ファイル編集の手順\n\n"
    "ファイルを編集する前に read_file で該当箇所を確認すること。\n"
    "既存内容を確認せずに編集を行ってはならない。\n\n"
    "既存ファイルへの局所的な変更（関数 1 つの修正、docstring 追加、\n"
    "数行の追加・変更など）には str_replace を使うこと。\n"
    "write_file はファイル全体を上書きするため、局所編集に使うと\n"
    "意図しない損失が発生する。\n\n"
    "write_file は以下の場合のみ使うこと:\n"
    "- 新規ファイルの作成\n"
    "- 明示的にファイル全体を置き換える場合\n\n"
    "str_replace で old_str が見つからない、または複数箇所に存在する\n"
    "場合はエラーとなる。read_file で対象箇所を確認し、十分なコンテキストを\n"
    "含めた old_str を指定すること。\n\n"
    "## ツール実行失敗時の振る舞い\n\n"
    "ツール実行が失敗した場合、原因を断定的に推測してユーザーに\n"
    "報告してはならない。\n\n"
    "複数の可能性が考えられる場合は、確証のない推測を「対処法」として\n"
    "箇条書きにせず、状況を簡潔に説明してユーザーまたは追加のツール\n"
    "呼び出しによる切り分けを促すこと。\n\n"
    "特に bash の timeout エラーでは、複数の可能性（時間不足、\n"
    "ネットワーク、プロセス停止、コマンド誤り等）があるため、\n"
    "これらを断定的に列挙せず、まずは timeout を増やして再試行する\n"
    "選択肢を提案すること。\n\n"
    "---\n\n"
    "## ユーザー承認について\n\n"
    "write_file と bash の実行前に、ユーザーは承認プロンプトを受け取る。\n"
    "ユーザーが Deny / Ctrl+C を選んだ場合、tool_result は\n"
    '"USER_DENIED: ..." で始まる文字列になる。\n\n'
    "USER_DENIED が返ってきた場合:\n"
    "- これはユーザーの意思による拒否であり、システムエラーやファイル権限の\n"
    "  問題ではない。原因を推測しない。\n"
    "- 「ファイルが読み取り専用」「権限がない」「パターンが原因」などの\n"
    "  技術的推測を一切しない。\n"
    "- ユーザーに何をしたいか確認するか、別のアプローチ（読み取り、別パス、\n"
    "  別コマンドなど）を提案する。\n"
    "- USER_DENIED は過去の一度のツール実行に対する拒否であり、その後の\n"
    "  ユーザーの新しい指示には影響しない。ユーザーが改めて同じ種類の\n"
    "  操作を指示した場合は、躊躇せずツールを呼び出して再度承認を求めること。\n"
    "  過去の拒否履歴を根拠にツール呼び出しをスキップしてはならない。\n"
    "  各ツール呼び出しは独立した判断であり、承認プロンプトはユーザーの\n"
    "  意思を確認する正しい手段である。"
)


def _build_system_prompt(plan_mode: bool, think_mode: str) -> str:
    content = _SYSTEM_PROMPT
    if plan_mode:
        content = _PLAN_SYSTEM_PROMPT + "\n\n" + _SYSTEM_PROMPT
    if think_mode == "off":
        content += "\n\n/no_think"
    return content


def chat_turn(
    messages: list,
    user_input: str,
    model: str,
    client,
    plan_mode: bool = False,
    think_mode: str = "show",
    allowed_write_paths: set[str] | None = None,
    allowed_bash_commands: set[str] | None = None,
    session_log: SessionLog | None = None,
) -> None:
    """Process one user input, including any tool-use loops."""
    messages.append({"role": "user", "content": user_input})
    if session_log:
        session_log.user_message(user_input)

    if allowed_write_paths is None:
        allowed_write_paths = set()
    if allowed_bash_commands is None:
        allowed_bash_commands = set()

    call_count = 0
    recent_calls: collections.deque = collections.deque(maxlen=3)
    turn_start = time.monotonic()

    while True:
        send_messages = [{"role": "system", "content": _build_system_prompt(plan_mode, think_mode)}] + messages
        llm_start = time.monotonic()

        with ThinkingIndicator():
            response = client.chat(
                model=model,
                messages=send_messages,
                tools=TOOL_SCHEMAS,
                think=(think_mode == "off"),
            )
        msg = response["message"]
        messages.append(msg)
        if session_log:
            session_log.llm_call(send_messages, _to_dict(msg), int((time.monotonic() - llm_start) * 1000))

        tool_calls = msg.get("tool_calls")
        if not tool_calls:
            # 通常のテキスト応答 → ターン終了
            content = msg.get("content", "")
            if think_mode == "hide":
                stripper = ThinkStripper()
                content = stripper.feed(content) + stripper.flush()
            if session_log:
                session_log.assistant_message(content, int((time.monotonic() - turn_start) * 1000))
            print(f"\nDarkClaude: {content}\n")
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

            if session_log:
                session_log.tool_call(name, args)

            # 承認ゲート（Plan モード OFF かつ副作用ツールのみ）
            if not plan_mode and name in ("write_file", "bash", "str_replace"):
                if name in ("write_file", "str_replace"):
                    key = args.get("path", "")
                    allowed_set = allowed_write_paths
                else:
                    key = args.get("command", "").strip()
                    allowed_set = allowed_bash_commands

                if not key:
                    preview = str(args)[:80]
                    print(f"  [tool] {name}({preview}) -> denied (invalid args)")
                    messages.append({"role": "tool", "content": "ERROR: ツールの引数が不正です（path または command が空）", "name": name})
                    continue

                if key not in allowed_set:
                    decision = request_approval(name, args)
                    if session_log:
                        session_log.approval(name, args, decision)
                    if decision == "always_allow":
                        allowed_set.add(key)
                    elif decision == "deny":
                        preview = str(args)[:80]
                        print(f"  [tool] {name}({preview}) -> USER_DENIED")
                        denied_msg = (
                            "USER_DENIED: あなた（ユーザー）がこのツールの実行を拒否しました。"
                            "ファイル権限などシステムの問題ではありません。"
                            "別のアプローチを提案するか、何をしたいか確認してください。"
                        )
                        if session_log:
                            session_log.tool_result(name, args, denied_msg, True)
                        messages.append({
                            "role": "tool",
                            "content": denied_msg,
                            "name": name,
                        })
                        continue

            tool_start = time.monotonic()
            result = dispatch(name, args, plan_mode=plan_mode)
            tool_elapsed = time.monotonic() - tool_start
            if session_log:
                session_log.tool_result(name, args, result, False)

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
    think_mode: str = config.get("think_mode", DEFAULT_THINK_MODE)
    logging_enabled: bool = config.get("logging_enabled", DEFAULT_LOGGING_ENABLED)
    if think_mode not in THINK_MODES:
        print(f"[warn] Invalid think_mode '{think_mode}' in config.json, falling back to 'show'.")
        think_mode = DEFAULT_THINK_MODE
    if not isinstance(logging_enabled, bool):
        print(f"[warn] Invalid logging_enabled '{logging_enabled}' in config.json, falling back to {DEFAULT_LOGGING_ENABLED}.")
        logging_enabled = DEFAULT_LOGGING_ENABLED
    if ("think_mode" not in config or config.get("think_mode") != think_mode or
            "logging_enabled" not in config):
        save_config({"model": model, "think_mode": think_mode, "logging_enabled": logging_enabled})
    messages: list = []
    plan_mode: bool = False
    allowed_write_paths: set[str] = set()
    allowed_bash_commands: set[str] = set()
    _data_dir = Path(__file__).parent / "data" / "conversations"
    session_log = SessionLog(
        enabled=logging_enabled,
        base_dir=_data_dir,
        dc_version="v0.7",
        model=model,
        plan_mode=plan_mode,
        think_mode=think_mode,
        system_prompt=_build_system_prompt(plan_mode, think_mode),
    )
    session_log.session_start()

    # ASCII art logo (ASCII characters only, codepage非依存)
    print(r"""
 ____             _     ____ _                _
|  _ \  __ _ _ __| | __/ ___| | __ _ _   _  __| | ___
| | | |/ _` | '__| |/ / |   | |/ _` | | | |/ _` |/ _ \
| |_| | (_| | |  |   <| |___| | (_| | |_| | (_| |  __/
|____/ \__,_|_|  |_|\_\\____|_|\__,_|\__,_|\__,_|\___|
                                              v0.7
""")

    # 起動時モデル存在チェック（Ollama 未起動時は例外を捕捉してスキップ）
    client = get_client(config)
    try:
        _available = client.list_models()
        if _available and model not in _available:
            if FALLBACK_MODEL not in _available:
                print(
                    f"ERROR: Configured model '{model}' is not available, "
                    f"and fallback '{FALLBACK_MODEL}' is also missing."
                )
                sys.exit(1)
            print(f"[warn] Configured model '{model}' not available.")
            print(f"[warn] Falling back to '{FALLBACK_MODEL}'.")
            model = FALLBACK_MODEL
            save_config({**config, "model": model})
    except Exception:
        pass  # Ollama 未起動等 → チェックをスキップ、最初のチャットでエラーが出る

    if session_log.enabled and session_log.file_path is not None:
        print(f"[logging] Recording to {session_log.file_path}")
    else:
        print("[logging] Disabled (set logging_enabled: true in config.json to enable)")
    print(f"Model: {model}")
    print("Commands: /exit /quit /bye  |  /models  |  /model <name>  |  /setmodel <name>  |  /plan  |  /think [show|hide|off]  |  /logging")
    print()

    _bindings = KeyBindings()

    @_bindings.add("enter")
    def _(event):
        buf = event.current_buffer
        if buf.text.endswith("\\"):
            buf.delete_before_cursor(1)
            buf.insert_text("\n")
        else:
            buf.validate_and_handle()

    _session = PromptSession(
        history=InMemoryHistory(),
        key_bindings=_bindings,
        multiline=False,
        prompt_continuation=lambda width, line_number, is_soft_wrap: "... ",
    )

    try:
        while True:
            think_tag = "" if think_mode == "show" else (" [HIDE]" if think_mode == "hide" else " [NOTHINK]")
            plan_tag = " [PLAN]" if plan_mode else ""
            log_tag = "" if session_log.enabled else " [NOLOG]"
            prompt_str = f"User{plan_tag}{think_tag}{log_tag} > "
            user_input = _session.prompt(prompt_str).strip()
            if not user_input:
                continue

            # 終了
            if user_input in ["/exit", "/quit", "/bye"]:
                print("Goodbye!")
                session_log.close("user_exit")
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
                    installed = get_installed_models(client)
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
                    installed = get_installed_models(client)
                    if name not in installed:
                        print(f"Warning: '{name}' not found. config.json is unchanged.")
                        if installed:
                            print(f"Installed: {', '.join(installed)}")
                    else:
                        model = name
                        save_config({"model": model, "think_mode": think_mode, "logging_enabled": logging_enabled})
                        print(f"Switched to: {model} (saved to config.json)")
                continue

            # Plan モードトグル
            if user_input == "/plan":
                plan_mode = not plan_mode
                status = "ON" if plan_mode else "OFF"
                print(f"Plan モード: {status}")
                session_log.update_context(plan_mode=plan_mode)
                continue

            # ログ収集制御
            if user_input == "/logging" or user_input.startswith("/logging "):
                arg = user_input[9:].strip() if user_input.startswith("/logging ") else ""
                if arg == "on":
                    enabled = session_log.set_enabled(True)
                elif arg == "off":
                    enabled = session_log.set_enabled(False)
                elif arg == "status":
                    enabled = session_log.enabled
                elif not arg:
                    enabled = session_log.toggle()
                else:
                    print(f"ERROR: invalid logging arg '{arg}'. Use: on | off | status")
                    continue
                status = "ON" if enabled else "OFF"
                if enabled and session_log.file_path:
                    print(f"ログ収集: {status} ({session_log.file_path})")
                else:
                    print(f"ログ収集: {status}")
                continue

            # 思考モード切り替え
            if user_input == "/think" or user_input.startswith("/think "):
                arg = user_input[7:].strip() if user_input.startswith("/think ") else ""
                if not arg:
                    idx = THINK_MODES.index(think_mode)
                    new_mode = THINK_MODES[(idx + 1) % len(THINK_MODES)]
                elif arg in THINK_MODES:
                    new_mode = arg
                else:
                    print(f"ERROR: invalid think mode '{arg}'. Use: show | hide | off")
                    continue
                old_mode = think_mode
                think_mode = new_mode
                save_config({"model": model, "think_mode": think_mode, "logging_enabled": logging_enabled})
                session_log.update_context(think_mode=think_mode)
                print(f"Think mode: {think_mode.upper()} (was {old_mode.upper()})")
                continue

            chat_turn(
                messages, user_input, model, client,
                plan_mode=plan_mode,
                think_mode=think_mode,
                allowed_write_paths=allowed_write_paths,
                allowed_bash_commands=allowed_bash_commands,
                session_log=session_log,
            )

    except (KeyboardInterrupt, EOFError):
        print("\nCtrl+C detected. Exiting safely.")
        session_log.close("ctrl_c")


if __name__ == "__main__":
    main()
