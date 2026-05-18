"""チャットターン処理 — OutputBuffer を使った TUI 版。"""
import collections
import json
import random
import threading
import time
from typing import Callable

from tools.registry import TOOL_SCHEMAS, dispatch
from session_log import SessionLog
from prompts import SYSTEM_PROMPT, PLAN_SYSTEM_PROMPT
from .output import OutputBuffer

_THINKING_VERBS = [
    "Thinking", "Cooking", "Brewing", "Cogitating",
    "Crunching", "Pondering", "Simmering",
    "思考中", "考え中", "推論中", "解析中", "演算中", "思索中", "分析中",
]


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


class TUIThinkingIndicator:
    """TUI 用の思考中インジケーター。ステータスラインに経過時間を表示する。"""

    def __init__(self, output: OutputBuffer, state: dict, app) -> None:
        self._output = output
        self._state = state
        self._app = app
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._verb = ""
        self._start = 0.0

    def _run(self) -> None:
        while not self._stop.wait(1.0):
            elapsed = int(time.monotonic() - self._start)
            self._state["thinking"] = f"✻ {self._verb} {elapsed}s"
            if self._app:
                self._app.invalidate()

    def __enter__(self) -> "TUIThinkingIndicator":
        self._verb = random.choice(_THINKING_VERBS)
        self._start = time.monotonic()
        self._state["thinking"] = f"✻ {self._verb} 0s"
        self._stop.clear()
        self._output.append(f"✻ {self._verb}...\n")
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *_) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)
        self._state["thinking"] = ""
        if self._app:
            self._app.invalidate()


def build_system_prompt(plan_mode: bool, think_mode: str) -> str:
    content = SYSTEM_PROMPT
    if plan_mode:
        content = PLAN_SYSTEM_PROMPT + "\n\n" + SYSTEM_PROMPT
    if think_mode == "off":
        content += "\n\n/no_think"
    return content


def _to_dict(obj) -> dict:
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


def _fmt_tool_call(name: str, args: dict) -> str:
    """⏺ ToolName(arg) 形式の表示文字列を生成する。"""
    for key in ("path", "command", "pattern", "query"):
        if key in args:
            val = str(args[key]).replace("\n", "↵")
            if len(val) > 47:
                val = val[:47] + "..."
            return f"⏺ {name}({val})\n"
    if args:
        first_val = str(next(iter(args.values()))).replace("\n", "↵")
        if len(first_val) > 47:
            first_val = first_val[:47] + "..."
        return f"⏺ {name}({first_val})\n"
    return f"⏺ {name}()\n"


def _fmt_tool_result(result: str) -> str:
    """  ⎿ <要約> 形式の表示文字列を生成する。"""
    summary = result.replace("\n", " ").strip()
    if len(summary) > 100:
        summary = summary[:100] + "..."
    return f"  ⎿ {summary}\n"


def chat_turn(
    output: OutputBuffer,
    state: dict,
    app,
    messages: list,
    user_input: str,
    model: str,
    client,
    plan_mode: bool = False,
    think_mode: str = "show",
    allowed_write_paths: set | None = None,
    allowed_bash_commands: set | None = None,
    session_log: SessionLog | None = None,
    approval_fn: Callable | None = None,
) -> None:
    """1 ターン分の処理（ユーザー入力 → ツールループ → アシスタント応答）。"""

    # ユーザー入力エコー
    output.append(f"▸ {user_input}\n\n")

    messages.append({"role": "user", "content": user_input})
    if session_log:
        session_log.user_message(user_input)

    if allowed_write_paths is None:
        allowed_write_paths = set()
    if allowed_bash_commands is None:
        allowed_bash_commands = set()
    if approval_fn is None:
        from tools.approval import request_approval
        approval_fn = request_approval

    call_count = 0
    recent_calls: collections.deque = collections.deque(maxlen=3)
    turn_start = time.monotonic()

    while True:
        send_messages = (
            [{"role": "system", "content": build_system_prompt(plan_mode, think_mode)}]
            + messages
        )
        llm_start = time.monotonic()

        with TUIThinkingIndicator(output, state, app):
            response = client.chat(
                model=model,
                messages=send_messages,
                tools=TOOL_SCHEMAS,
                think=(think_mode == "off"),
            )

        msg = response["message"]
        messages.append(msg)
        if session_log:
            session_log.llm_call(
                send_messages,
                _to_dict(msg),
                int((time.monotonic() - llm_start) * 1000),
            )

        tool_calls = msg.get("tool_calls")
        if not tool_calls:
            # テキスト応答 → ターン終了
            content = msg.get("content", "")
            if think_mode == "hide":
                stripper = ThinkStripper()
                content = stripper.feed(content) + stripper.flush()
            if session_log:
                session_log.assistant_message(
                    content, int((time.monotonic() - turn_start) * 1000)
                )
            elapsed = time.monotonic() - turn_start
            output.append(f"\nDarkClaude: {content}\n\n")
            output.append(f"  (合計 {elapsed:.1f}s)\n\n")
            return

        # ツール呼び出しを順に実行
        limit_reached = False
        for call in tool_calls:
            name = call["function"]["name"]
            args = call["function"]["arguments"]

            # ターン内上限チェック（25回）
            call_count += 1
            if call_count > 25:
                error = (
                    "ERROR: このターンの tool_call 回数が上限（25回）に達しました。"
                    "タスクを分割するか、再度指示してください。"
                )
                output.append(f"  ⏺ {name}(...) → 上限到達でブロック\n")
                messages.append({"role": "tool", "content": error, "name": name})
                limit_reached = True
                break

            # 連続同一呼び出し検出
            call_key = (name, json.dumps(args, sort_keys=True, ensure_ascii=False))
            if len(recent_calls) == 3 and all(k == call_key for k in recent_calls):
                error = (
                    "ERROR: 同じツール呼び出しが3回繰り返されました。"
                    "引数を変えるか、別のアプローチを試してください。"
                )
                output.append(f"  ⏺ {name}(...) → 連続同一呼び出しでブロック\n")
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
                    output.append(
                        f"  ⏺ {name}({str(args)[:50]}) → invalid args\n"
                    )
                    messages.append({
                        "role": "tool",
                        "content": "ERROR: ツールの引数が不正です（path または command が空）",
                        "name": name,
                    })
                    continue

                if key not in allowed_set:
                    decision = approval_fn(name, args)
                    if session_log:
                        session_log.approval(name, args, decision)
                    if decision == "always_allow":
                        allowed_set.add(key)
                    elif decision == "deny":
                        output.append(f"  ⏺ {name}({key[:50]}) → USER_DENIED\n")
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

            # ツール呼び出し表示
            output.append(_fmt_tool_call(name, args))

            tool_start = time.monotonic()
            result = dispatch(name, args, plan_mode=plan_mode)
            tool_elapsed = time.monotonic() - tool_start

            if session_log:
                session_log.tool_result(name, args, result, False)

            output.append(_fmt_tool_result(result))
            output.append(
                f"  ({tool_elapsed:.1f}s)\n"
            )

            messages.append({
                "role": "tool",
                "content": result,
                "name": name,
            })

        if limit_reached:
            output.append(
                "\n[安全機構] ターン内 tool_call 上限（25回）に達しました。"
                "処理を中断します。\n\n"
            )
            return
        # 次のループへ（モデルにツール結果を渡して続きを生成させる）
