banner = """ ██████╗  █████╗ ██████╗ ██╗  ██╗ ██████╗██╗      █████╗ ██╗   ██╗██████╗ ███████╗
 ██╔══██╗██╔══██╗██╔══██╗██║ ██╔╝██╔════╝██║     ██╔══██╗██║   ██║██╔══██╗██╔════╝
 ██║  ██║███████║██████╔╝█████╔╝ ██║     ██║     ███████║██║   ██║██║  ██║█████╗
 ██║  ██║██╔══██║██╔══██╗██╔═██╗ ██║     ██║     ██╔══██║██║   ██║██║  ██║██╔══╝
 ██████╔╝██║  ██║██║  ██║██║  ██╗╚██████╗███████╗██║  ██║╚██████╔╝██████╔╝███████╗
 ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚══════╝"""

mascot = """   █        █
   ██      ██
  ██▀██████▀██
    ██▄ ████ ▄██
  ████████████████
  ████████████
   █ █    █ █"""

code = '''# -*- coding: utf-8 -*-
"""DarkClaude Textual TUI (Phase B) - v0.9-beta UI 仕様準拠"""
import sys, asyncio, json, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from textual.app import App, ComposeResult
from textual.widgets import Input, RichLog, Static
from textual.containers import Vertical

_CONFIG_PATH = Path(__file__).parent.parent / "config.json"
VERSION = "v0.9-beta"

BANNER_LINES = ''' + repr(banner.split("\n")) + '''
MASCOT_LINES = ''' + repr(mascot.split("\n")) + '''

def _load_config():
    try:
        return json.loads(_CONFIG_PATH.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}


def render_banner_mascot() -> str:
    """banner + mascot を Rich markup で1文字列に組み立てる"""
    banner_width = max(len(line) for line in BANNER_LINES)
    GAP = "  "
    lines = []
    # 行0: 空白 + GAP + mascot[0]
    lines.append(" " * banner_width + GAP + f"[#2a2a2a bold]{MASCOT_LINES[0]}[/]")
    # 行1-6: banner[i] + GAP + mascot[i+1]
    for i in range(6):
        lines.append(f"[#2a2a2a bold]{BANNER_LINES[i]}[/]" + GAP + f"[#2a2a2a bold]{MASCOT_LINES[i+1]}[/]")
    return "\\n".join(lines)


class StatusBar(Static):
    DEFAULT_CSS = """
    StatusBar {
        height: 1;
        background: #0a0a0a;
        color: #6a6a6a;
        padding: 0 1;
    }
    """
    def update_status(self, text: str) -> None:
        self.update(text)


class ChatLog(RichLog):
    DEFAULT_CSS = """
    ChatLog {
        height: 1fr;
        background: #0a0a0a;
        color: #e0e0e0;
        border: none;
        padding: 0 1;
        scrollbar-gutter: stable;
        scrollbar-color: #3a3a3a #0a0a0a;
    }
    """


class InputArea(Static):
    """上下ライン構造の入力エリア (Frame ではない、仕様準拠)"""
    DEFAULT_CSS = """
    InputArea {
        height: 3;
        background: #0a0a0a;
    }
    InputArea Static.separator {
        height: 1;
        color: #3a3a3a;
    }
    InputArea Input {
        height: 1;
        background: #0a0a0a;
        color: #e0e0e0;
        border: none;
        padding: 0;
    }
    """
    def compose(self) -> ComposeResult:
        yield Static("─" * 200, classes="separator")
        yield Input(placeholder="", id="input-area")
        yield Static("─" * 200, classes="separator")


class DarkClaudeApp(App):
    CSS = """
    Screen {
        background: #0a0a0a;
        layout: vertical;
    }
    """
    BINDINGS = [
        ("ctrl+c", "quit", "終了"),
        ("ctrl+l", "clear_log", "クリア"),
    ]

    def __init__(self):
        super().__init__()
        self.config = _load_config()
        self.model = self.config.get("model", "qwen3.6")
        self.harness = self.config.get("harness_mode", "claude_compat")
        self.messages = []
        self.start_time = time.time()
        from clients import get_client
        self.client = get_client(self.config)

    def compose(self) -> ComposeResult:
        yield ChatLog(id="chat-log", markup=True, highlight=True)
        yield InputArea()
        yield StatusBar("", id="status-bar")

    def on_mount(self) -> None:
        log = self.query_one(ChatLog)
        # バナー + マスコット
        log.write(render_banner_mascot())
        log.write("")
        # 情報行
        cwd = str(Path.cwd())
        if len(cwd) > 50:
            cwd = "..." + cwd[-47:]
        harness_label = "darkclaude-native" if self.harness == "darkclaude_native" else "claude-compat"
        log.write(f" [#6a6a6a]version    [/][#b095d5]{VERSION}[/]")
        log.write(f" [#6a6a6a]model      [/][#5a8a98]{self.model}[/]")
        log.write(f" [#6a6a6a]server     [/][#5a8a98]{self.config.get('base_url','http://localhost:8080')}[/]")
        log.write(f" [#6a6a6a]cwd        [/][#e0e0e0]{cwd}[/]")
        log.write(f" [#6a6a6a]phase      [/][#b095d5]A6 stabilization[/]")
        log.write(f" [#6a6a6a]harness    [/][#b095d5]{harness_label}[/]")
        log.write("")
        log.write(" [#6a6a6a]Type /help for commands.  Ctrl+C to exit.[/]")
        log.write("")
        self._update_status_bar()
        self.query_one(Input).focus()

    def _update_status_bar(self, thinking: str = "") -> None:
        status = self.query_one(StatusBar)
        elapsed = int(time.time() - self.start_time)
        m, s = divmod(elapsed, 60)
        time_str = f"{m}m {s:02d}s"
        thinking_part = f"  [#b095d5]{thinking}[/]" if thinking else ""
        left = (
            f"[#5a8a98]{self.model}[/] "
            f"[#6a6a6a]·[/] [#b095d5]Phase A6 stabilization[/]  "
            f"[#6a6a6a]·[/]  [#6a6a6a]Ctrl+Y: copy mode[/]"
            f"{thinking_part}"
        )
        right = f"[#5a8a98]⏱ {time_str}[/]"
        status.update_status(f"{left}    {right}")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        if not text:
            return
        event.input.clear()
        if text.startswith("/"):
            self._handle_command(text)
        else:
            log = self.query_one(ChatLog)
            # ユーザー入力 echo: bg #1a1a1a + 白 bold ▸ + 灰 text
            log.write(f"[on #1a1a1a] [bold white]▸[/] [#7a7a7a]{text}[/][/]")
            self.run_worker(self._ai_turn(text), exclusive=True)

    async def _ai_turn(self, user_input: str) -> None:
        from tools.registry import TOOL_SCHEMAS, dispatch
        import random
        log = self.query_one(ChatLog)
        verbs = ["Thinking", "Cooking", "Brewing", "Pondering", "推論中", "解析中", "思索中"]
        verb = random.choice(verbs)
        log.write(f"[#b095d5]✻ {verb}...[/]")
        self._update_status_bar(thinking=f"✻ {verb}")
        self.messages.append({"role": "user", "content": user_input})
        try:
            while True:
                response = await asyncio.to_thread(
                    self.client.chat, self.model, self.messages, TOOL_SCHEMAS,
                )
                msg = response.get("message", {})
                self.messages.append(msg)
                tool_calls = msg.get("tool_calls") or []
                if not tool_calls:
                    content = msg.get("content", "")
                    log.write(f"[#e0e0e0]{content}[/]")
                    log.write("")
                    break
                for tc in tool_calls:
                    name = tc.get("function", {}).get("name", "")
                    args = tc.get("function", {}).get("arguments", {})
                    # 主要引数の優先順: path > command > pattern > query
                    key_val = ""
                    for k in ("path", "command", "pattern", "query"):
                        if k in args:
                            key_val = str(args[k])
                            break
                    if not key_val and args:
                        key_val = str(next(iter(args.values())))
                    if len(key_val) > 47:
                        key_val = key_val[:44] + "..."
                    key_val = key_val.replace("\\n", "↵")
                    t_start = time.time()
                    log.write(f"[#5a8a98]⏺ {name}({key_val})[/]")
                    result = await asyncio.to_thread(dispatch, name, args)
                    elapsed = time.time() - t_start
                    # 結果要約
                    summary = result[:100].replace("\\n", " ")
                    if len(result) > 100:
                        summary += "..."
                    is_error = result.startswith("ERROR:")
                    color = "#a85050" if is_error else "#5a8a98"
                    log.write(f"  [{color}]⎿ {summary}[/] [#6a6a6a]({elapsed:.1f}s)[/]")
                    self.messages.append({"role": "tool", "content": result, "name": name})
        except Exception as e:
            log.write(f"[bold #a85050]ERROR:[/] {e}")
        finally:
            self._update_status_bar()

    def _handle_command(self, cmd: str) -> None:
        log = self.query_one(ChatLog)
        if cmd in ("/exit", "/quit", "/bye"):
            self.exit()
        elif cmd == "/clear":
            self.action_clear_log()
            self.messages.clear()
        elif cmd == "/help":
            log.write("[#6a6a6a]  /exit /clear /help[/]")
        else:
            log.write(f"[#a85050]  unknown:[/] {cmd}")

    def action_clear_log(self) -> None:
        self.query_one(ChatLog).clear()


def run() -> None:
    DarkClaudeApp().run()


if __name__ == "__main__":
    run()
'''

with open("tui/textual_app.py", "w", encoding="utf-8") as f:
    f.write(code)
print("done")
