"""DarkClaude TUI Application (v0.9-beta) — フルスクリーン REPL 本体。"""
import asyncio
import atexit
import json
import sys
import threading
import time
from pathlib import Path

from prompt_toolkit import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.filters import Condition
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.key_binding import KeyBindings, merge_key_bindings
from prompt_toolkit.layout.containers import ConditionalContainer, HSplit, Window
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.dimension import D
from prompt_toolkit.layout.layout import Layout

from .style import DARKCLAUDE_STYLE
from .banner import render_banner
from .output import OutputBuffer
from .status import make_status_fn
from .chat import chat_turn, build_system_prompt
from .approval import ApprovalDialog, decision_from_index
from .copy_mode import CopyMode
from . import progress as prog
from clients import get_client
from session_log import SessionLog

# ---- 定数 ----

DEFAULT_MODEL = "qwen3:8b"
FALLBACK_MODEL = "qwen3:8b"
DEFAULT_THINK_MODE = "show"
THINK_MODES = ("show", "hide", "off")
DEFAULT_LOGGING_ENABLED = True
_CONFIG_PATH = Path(__file__).parent.parent / "config.json"

_HELP_TEXT = """\
Commands:
  /exit /quit /bye        — 終了
  /help                   — このヘルプを表示
  /clear                  — 出力エリアをクリア
  /plan                   — Plan モードトグル
  /model [name]           — 現在のモデル確認 / 切り替え（セッション内）
  /setmodel <name>        — モデル切り替え（config.json に永続化）
  /think [show|hide|off]  — 思考モード切り替え
  /logging [on|off|status]— ログ収集制御

Keyboard:
  Enter         — 送信（末尾に自動スクロール）
  Ctrl+C        — 終了
  Ctrl+L        — 出力クリア
  Up / Down     — 入力履歴
  PageUp / PageDown / マウスホイール — 出力スクロール
  Home / End    — 最上 / 最下
  Ctrl+Y        — コピーモード開始
    ↑↓←→       — カーソル移動
    Shift+↑↓←→ — 選択範囲拡張
    v           — 選択開始 (Vim 風)
    y / Enter   — 選択テキストをコピー → 終了
    Esc / q     — コピーモード終了 (コピーしない)

"""


# ---- Config ----

def _load_config() -> dict:
    if _CONFIG_PATH.exists():
        try:
            return json.loads(_CONFIG_PATH.read_text(encoding="utf-8-sig"))
        except Exception:
            pass
    return {"model": DEFAULT_MODEL}


def _save_config(updates: dict) -> None:
    try:
        existing = json.loads(_CONFIG_PATH.read_text(encoding="utf-8-sig"))
        if not isinstance(existing, dict):
            existing = {}
    except Exception:
        existing = {}
    existing.update(updates)
    _CONFIG_PATH.write_text(
        json.dumps(existing, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# ---- エントリポイント ----

def run() -> None:
    """TUI を起動する。main.py から呼ばれる。"""

    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    # ---- 設定読み込み ----
    config = _load_config()
    model: str = config.get("model", DEFAULT_MODEL)
    think_mode: str = config.get("think_mode", DEFAULT_THINK_MODE)
    logging_enabled: bool = config.get("logging_enabled", DEFAULT_LOGGING_ENABLED)

    if think_mode not in THINK_MODES:
        think_mode = DEFAULT_THINK_MODE
    if not isinstance(logging_enabled, bool):
        logging_enabled = DEFAULT_LOGGING_ENABLED

    _save_config({"model": model, "think_mode": think_mode, "logging_enabled": logging_enabled})

    # ---- セッション状態 ----
    state: dict = {
        "model": model,
        "think_mode": think_mode,
        "logging_enabled": logging_enabled,
        "plan_mode": False,
        "thinking": "",
        "is_busy": False,
    }
    messages: list = []
    allowed_write_paths: set[str] = set()
    allowed_bash_commands: set[str] = set()

    # ---- クライアント ----
    client = get_client(config)
    try:
        available = client.list_models()
        if available and model not in available:
            if FALLBACK_MODEL in available:
                model = FALLBACK_MODEL
                state["model"] = model
                _save_config({"model": model})
    except Exception:
        pass

    # ---- セッションログ ----
    _data_dir = Path(__file__).parent.parent / "data" / "conversations"
    session_log = SessionLog(
        enabled=logging_enabled,
        base_dir=_data_dir,
        dc_version="v0.9-beta",
        model=model,
        plan_mode=state["plan_mode"],
        think_mode=think_mode,
        system_prompt=build_system_prompt(state["plan_mode"], think_mode),
    )
    session_log.session_start()

    # ---- OutputBuffer ----
    output = OutputBuffer()
    start_time = time.time()

    # ---- 入力 Buffer ----
    input_buf = Buffer(name="input", multiline=False, history=InMemoryHistory())

    # ---- 承認 Dialog ----
    approval = ApprovalDialog()

    # ---- コピーモード ----
    copy_mode = CopyMode()

    # app / loop は起動後に格納
    _app_ref: list[Application | None] = [None]
    _loop_ref: list[asyncio.AbstractEventLoop | None] = [None]

    # ---- ステータスライン ----
    get_status = make_status_fn(state, start_time, copy_mode=copy_mode)

    # ---- 承認関数 (TUI ネイティブ Dialog 版) ----
    def _make_approval_fn(app: Application) -> object:
        def approval_fn(name: str, args: dict) -> str:
            loop = _loop_ref[0]
            if loop is None:
                # フォールバック: questionary 直接呼び出し
                from tools.approval import request_approval
                return request_approval(name, args)

            # コマンド文字列の組み立て
            if name == "bash":
                cmd_text = args.get("command", "")
                title = "Bash command"
                emphasis = cmd_text[:60]
            elif name == "write_file":
                path = args.get("path", "")
                cmd_text = f"Write to: {path}"
                title = "Write file"
                emphasis = path
            elif name == "str_replace":
                path = args.get("path", "")
                old_s = str(args.get("old_str", ""))[:80].replace("\n", "↵")
                new_s = str(args.get("new_str", ""))[:80].replace("\n", "↵")
                cmd_text = f"Path: {path}\n- {old_s}\n+ {new_s}"
                title = "Edit file"
                emphasis = path
            else:
                cmd_text = str(args)[:120]
                title = name
                emphasis = name

            result_holder: list[int] = [-1]
            done_ev = threading.Event()

            async def _show_dialog() -> None:
                idx = await approval.show(title, cmd_text, emphasis=emphasis)
                result_holder[0] = idx
                done_ev.set()
                app.invalidate()

            future = asyncio.run_coroutine_threadsafe(_show_dialog(), loop)
            done_ev.wait(timeout=300)

            idx = result_holder[0]
            if idx < 0:
                return "deny"
            return decision_from_index(idx)

        return approval_fn

    # ---- コマンドハンドラ ----
    def handle_command(text: str) -> bool:
        app = _app_ref[0]

        if text in ("/exit", "/quit", "/bye"):
            output.append("Goodbye!\n")
            session_log.close("user_exit")
            prog.clear()
            if app:
                app.exit()
            return True

        if text == "/help":
            output.append(_HELP_TEXT)
            return True

        if text == "/clear":
            output.clear()
            return True

        if text == "/plan":
            state["plan_mode"] = not state["plan_mode"]
            status = "ON" if state["plan_mode"] else "OFF"
            output.append(f"Plan モード: {status}\n\n")
            session_log.update_context(plan_mode=state["plan_mode"])
            return True

        if text == "/model" or text.startswith("/model "):
            name = text[7:].strip() if text.startswith("/model ") else ""
            if not name:
                output.append(f"Current model: {state['model']}\n\n")
            else:
                try:
                    installed = client.list_models()
                    if name not in installed:
                        output.append(f"Warning: '{name}' not found.\n")
                        if installed:
                            output.append(f"Installed: {', '.join(installed)}\n\n")
                    else:
                        state["model"] = name
                        output.append(f"Switched to: {name}\n\n")
                except Exception as e:
                    output.append(f"Error listing models: {e}\n\n")
            return True

        if text == "/setmodel" or text.startswith("/setmodel "):
            name = text[10:].strip() if text.startswith("/setmodel ") else ""
            if not name:
                output.append("Usage: /setmodel <name>\n\n")
            else:
                try:
                    installed = client.list_models()
                    if name not in installed:
                        output.append(
                            f"Warning: '{name}' not found. config.json は変更されません。\n\n"
                        )
                        if installed:
                            output.append(f"Installed: {', '.join(installed)}\n\n")
                    else:
                        state["model"] = name
                        _save_config({
                            "model": name,
                            "think_mode": state["think_mode"],
                            "logging_enabled": state["logging_enabled"],
                        })
                        output.append(f"Switched to: {name} (saved to config.json)\n\n")
                except Exception as e:
                    output.append(f"Error: {e}\n\n")
            return True

        if text == "/think" or text.startswith("/think "):
            arg = text[7:].strip() if text.startswith("/think ") else ""
            if not arg:
                idx = THINK_MODES.index(state["think_mode"])
                new_mode = THINK_MODES[(idx + 1) % len(THINK_MODES)]
            elif arg in THINK_MODES:
                new_mode = arg
            else:
                output.append(f"ERROR: invalid think mode '{arg}'. Use: show | hide | off\n\n")
                return True
            old_mode = state["think_mode"]
            state["think_mode"] = new_mode
            _save_config({
                "model": state["model"],
                "think_mode": new_mode,
                "logging_enabled": state["logging_enabled"],
            })
            session_log.update_context(think_mode=new_mode)
            output.append(f"Think mode: {new_mode.upper()} (was {old_mode.upper()})\n\n")
            return True

        if text == "/logging" or text.startswith("/logging "):
            arg = text[9:].strip() if text.startswith("/logging ") else ""
            if arg == "on":
                enabled = session_log.set_enabled(True)
            elif arg == "off":
                enabled = session_log.set_enabled(False)
            elif arg == "status":
                enabled = session_log.enabled
            elif not arg:
                enabled = session_log.toggle()
            else:
                output.append(f"ERROR: invalid logging arg '{arg}'. Use: on | off | status\n\n")
                return True
            state["logging_enabled"] = enabled
            status_str = "ON" if enabled else "OFF"
            if enabled and session_log.file_path:
                output.append(f"ログ収集: {status_str} ({session_log.file_path})\n\n")
            else:
                output.append(f"ログ収集: {status_str}\n\n")
            return True

        return False

    # ---- チャット実行 ----
    def _do_chat(text: str, app: Application) -> None:
        approval_fn = _make_approval_fn(app)
        try:
            chat_turn(
                output=output,
                state=state,
                app=app,
                messages=messages,
                user_input=text,
                model=state["model"],
                client=client,
                plan_mode=state["plan_mode"],
                think_mode=state["think_mode"],
                allowed_write_paths=allowed_write_paths,
                allowed_bash_commands=allowed_bash_commands,
                session_log=session_log,
                approval_fn=approval_fn,
            )
        except Exception as e:
            output.append(f"\n[ERROR] {type(e).__name__}: {e}\n\n")
        finally:
            state["is_busy"] = False
            app.invalidate()

    # ---- Layout パーツ ----

    # 出力エリア: FormattedTextControl でスタイル付き描画
    output_window = Window(
        content=FormattedTextControl(output.get_formatted_text, focusable=False),
        wrap_lines=True,
        height=D(weight=1),
    )
    output.window = output_window  # auto_scroll 用に参照を渡す

    # 承認 Dialog コンテナ (is_active=True の時だけ表示)
    approval_container = approval.make_container()

    # 入力エリア: 上ライン + 入力行 + 下ライン
    input_area = HSplit([
        Window(height=1, char="─", style="class:separator"),
        Window(
            content=BufferControl(buffer=input_buf, focusable=True),
            height=1,
            style="class:input",
        ),
        Window(height=1, char="─", style="class:separator"),
    ])

    # 承認中 or コピーモード中は入力エリアを非表示
    conditional_input = ConditionalContainer(
        content=input_area,
        filter=Condition(lambda: not approval.is_active and not copy_mode.is_active),
    )

    status_window = Window(
        content=FormattedTextControl(get_status),
        height=1,
        style="class:status",
    )

    layout = Layout(
        HSplit([
            output_window,
            approval_container,
            conditional_input,
            status_window,
        ]),
        focused_element=input_buf,
    )

    # ---- KeyBindings ----
    kb = KeyBindings()
    not_approval = Condition(lambda: not approval.is_active)

    @kb.add("enter", filter=not_approval)
    def _on_enter(event):
        if state["is_busy"]:
            return
        text = input_buf.text.strip()
        if not text:
            return
        input_buf.append_to_history()
        input_buf.reset()
        # Enter 送信で末尾に戻す
        output.auto_scroll = True
        output_window.vertical_scroll = 999999

        if handle_command(text):
            return

        state["is_busy"] = True
        t = threading.Thread(target=_do_chat, args=(text, event.app), daemon=True)
        t.start()

    @kb.add("c-c")
    @kb.add("c-d")
    def _on_exit(event):
        session_log.close("ctrl_c")
        prog.clear()
        event.app.exit()

    @kb.add("c-l")
    def _on_clear(event):
        output.clear()

    @kb.add("up", filter=not_approval)
    def _on_up(event):
        input_buf.history_backward()

    @kb.add("down", filter=not_approval)
    def _on_down(event):
        input_buf.history_forward()

    # ---- スクロール KeyBindings ----

    @kb.add("pageup", eager=True)
    def _on_pageup(event):
        output.auto_scroll = False
        if output_window.render_info:
            page_h = output_window.render_info.window_height
            output_window.vertical_scroll = max(
                0, output_window.vertical_scroll - page_h
            )
        event.app.invalidate()

    @kb.add("pagedown", eager=True)
    def _on_pagedown(event):
        if output_window.render_info:
            page_h = output_window.render_info.window_height
            content_h = output_window.render_info.content_height
            new_scroll = min(
                max(0, content_h - page_h),
                output_window.vertical_scroll + page_h,
            )
            output_window.vertical_scroll = new_scroll
            # 末尾まで来たら auto_scroll を再有効化
            if new_scroll >= max(0, content_h - page_h):
                output.auto_scroll = True
        event.app.invalidate()

    @kb.add("home", eager=True)
    def _on_home(event):
        output.auto_scroll = False
        output_window.vertical_scroll = 0
        event.app.invalidate()

    @kb.add("end", eager=True)
    def _on_end(event):
        output.auto_scroll = True
        output_window.vertical_scroll = 999999
        event.app.invalidate()

    @kb.add("c-y", eager=True)
    def _enter_copy_mode(event):
        """Ctrl+Y でコピーモードに入る。"""
        if not copy_mode.is_active and not approval.is_active:
            copy_mode.enter(output.get_plain_lines())
            event.app.invalidate()

    # 承認 Dialog + コピーモードの KeyBindings をマージ
    merged_kb = merge_key_bindings([kb, approval.make_keybindings(), copy_mode.make_keybindings()])

    # ---- Application ----
    app = Application(
        layout=layout,
        key_bindings=merged_kb,
        style=DARKCLAUDE_STYLE,
        full_screen=True,
        mouse_support=True,   # マウスホイールスクロール有効化
    )
    _app_ref[0] = app

    # 終了時に必ずタスクバー進捗をクリア
    atexit.register(prog.clear)

    # ---- 初期表示 ----
    output.append_fragments(list(render_banner(config)))
    if session_log.enabled and session_log.file_path is not None:
        output.append(f"[logging] Recording to {session_log.file_path}\n\n")
    else:
        output.append("[logging] Disabled\n\n")

    # ---- 起動 ----
    async def _run_async() -> None:
        _loop_ref[0] = asyncio.get_running_loop()
        await app.run_async()

    try:
        asyncio.run(_run_async())
    except KeyboardInterrupt:
        session_log.close("ctrl_c")
        prog.clear()
    except Exception:
        session_log.close("error")
        prog.clear()
        raise
