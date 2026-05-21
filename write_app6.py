import json
from pathlib import Path

# prompts.py から SYSTEM_PROMPT を取得して埋め込む
try:
    import sys
    sys.path.insert(0, ".")
    from prompts import SYSTEM_PROMPT
    system_prompt = SYSTEM_PROMPT
except:
    system_prompt = "あなたは DarkClaude です。ローカルで動作する AI アシスタントです。"

banner = """ \u2588\u2588\u2588\u2588\u2588\u2588\u2557  \u2588\u2588\u2588\u2588\u2588\u2557 \u2588\u2588\u2588\u2588\u2588\u2588\u2557 \u2588\u2588\u2557  \u2588\u2588\u2557 \u2588\u2588\u2588\u2588\u2588\u2588\u2557\u2588\u2588\u2557      \u2588\u2588\u2588\u2588\u2588\u2557 \u2588\u2588\u2557   \u2588\u2588\u2557\u2588\u2588\u2588\u2588\u2588\u2588\u2557 \u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2557
 \u2588\u2588\u2554\u2550\u2550\u2588\u2588\u2557\u2588\u2588\u2554\u2550\u2550\u2588\u2588\u2557\u2588\u2588\u2554\u2550\u2550\u2588\u2588\u2557\u2588\u2588\u2551 \u2588\u2588\u2554\u255d\u2588\u2588\u2554\u2550\u2550\u2550\u2550\u255d\u2588\u2588\u2551     \u2588\u2588\u2554\u2550\u2550\u2588\u2588\u2557\u2588\u2588\u2551   \u2588\u2588\u2551\u2588\u2588\u2554\u2550\u2550\u2588\u2588\u2557\u2588\u2588\u2554\u2550\u2550\u2550\u2550\u255d
 \u2588\u2588\u2551  \u2588\u2588\u2551\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2551\u2588\u2588\u2588\u2588\u2588\u2588\u2554\u255d\u2588\u2588\u2588\u2588\u2588\u2554\u255d \u2588\u2588\u2551     \u2588\u2588\u2551     \u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2551\u2588\u2588\u2551   \u2588\u2588\u2551\u2588\u2588\u2551  \u2588\u2588\u2551\u2588\u2588\u2588\u2588\u2588\u2557
 \u2588\u2588\u2551  \u2588\u2588\u2551\u2588\u2588\u2554\u2550\u2550\u2588\u2588\u2551\u2588\u2588\u2554\u2550\u2550\u2588\u2588\u2557\u2588\u2588\u2554\u2550\u2588\u2588\u2557 \u2588\u2588\u2551     \u2588\u2588\u2551     \u2588\u2588\u2554\u2550\u2550\u2588\u2588\u2551\u2588\u2588\u2551   \u2588\u2588\u2551\u2588\u2588\u2551  \u2588\u2588\u2551\u2588\u2588\u2554\u2550\u2550\u255d
 \u2588\u2588\u2588\u2588\u2588\u2588\u2554\u255d\u2588\u2588\u2551  \u2588\u2588\u2551\u2588\u2588\u2551  \u2588\u2588\u2551\u2588\u2588\u2551  \u2588\u2588\u2557\u255a\u2588\u2588\u2588\u2588\u2588\u2588\u2557\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2557\u2588\u2588\u2551  \u2588\u2588\u2551\u255a\u2588\u2588\u2588\u2588\u2588\u2588\u2554\u255d\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2557
 \u255a\u2550\u2550\u2550\u2550\u2550\u255d \u255a\u2550\u255d  \u255a\u2550\u255d\u255a\u2550\u255d  \u255a\u2550\u255d\u255a\u2550\u255d  \u255a\u2550\u255d \u255a\u2550\u2550\u2550\u2550\u2550\u255d\u255a\u2550\u2550\u2550\u2550\u2550\u2550\u255d\u255a\u2550\u255d  \u255a\u2550\u255d \u255a\u2550\u2550\u2550\u2550\u2550\u255d \u255a\u2550\u2550\u2550\u2550\u2550\u255d \u255a\u2550\u2550\u2550\u2550\u2550\u2550\u255d"""

mascot = """   \u2588        \u2588
   \u2588\u2588      \u2588\u2588
  \u2588\u2588\u2580\u2588\u2588\u2588\u2588\u2588\u2588\u2580\u2588\u2588
    \u2588\u2588\u2584 \u2588\u2588\u2588\u2588 \u2584\u2588\u2588
  \u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588
  \u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588
   \u2588 \u2588    \u2588 \u2588"""

code = '''# -*- coding: utf-8 -*-
import sys, asyncio, json, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from textual.app import App, ComposeResult
from textual.widgets import Input, RichLog, Static
from textual.containers import Horizontal, Vertical

_CONFIG_PATH = Path(__file__).parent.parent / "config.json"
VERSION = "v0.9-beta"
SYSTEM_PROMPT = ''' + repr(system_prompt) + '''

BANNER_LINES = ''' + repr(banner.split("\n")) + '''
MASCOT_LINES = ''' + repr(mascot.split("\n")) + '''

def _load_config():
    try:
        return json.loads(_CONFIG_PATH.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}

def render_banner_mascot():
    banner_width = max(len(line) for line in BANNER_LINES)
    GAP = "  "
    lines = []
    lines.append(" " * banner_width + GAP + "[#2a2a2a bold]" + MASCOT_LINES[0] + "[/]")
    for i in range(6):
        lines.append("[#2a2a2a bold]" + BANNER_LINES[i] + "[/]" + GAP + "[#2a2a2a bold]" + MASCOT_LINES[i+1] + "[/]")
    return "\\n".join(lines)


class StatusBar(Static):
    DEFAULT_CSS = """
    StatusBar {
        height: 1;
        background: #0a0a0a;
        color: #6a6a6a;
        padding: 0 1;
        dock: bottom;
    }
    """
    def update_status(self, text):
        self.update(text)


class ChatLog(RichLog):
    DEFAULT_CSS = """
    ChatLog {
        height: 1fr;
        background: #0a0a0a;
        color: #e0e0e0;
        border: none;
        padding: 0 1;
        margin: 0;
        scrollbar-size: 0 0;
    }
    """


class InputArea(Vertical):
    DEFAULT_CSS = """
    InputArea {
        height: 3;
        background: #0a0a0a;
        padding: 0;
        margin: 0;
    }
    InputArea .sep {
        height: 1;
        color: #3a3a3a;
        background: #0a0a0a;
        width: 1fr;
        padding: 0;
    }
    InputArea Horizontal {
        height: 1;
        background: #0a0a0a;
        padding: 0;
    }
    InputArea .prompt-char {
        width: 2;
        color: #ffffff;
        text-style: bold;
        background: #0a0a0a;
    }
    InputArea Input {
        width: 1fr;
        border: none;
        outline: none;
        background: #0a0a0a;
        color: #e0e0e0;
        padding: 0;
    }
    InputArea Input:focus { border: none; outline: none; }
    InputArea Input.-focused { border: none; }
    """
    def compose(self):
        yield Static("\u2500" * 400, classes="sep")
        with Horizontal():
            yield Static("\u25b8 ", classes="prompt-char")
            yield Input(placeholder="", id="input-area")
        yield Static("\u2500" * 400, classes="sep")


class DarkClaudeApp(App):
    TITLE = "DarkClaude"
    CSS = """
    Screen {
        background: #0a0a0a;
        layout: vertical;
        border: none;
        padding: 0;
        margin: 0;
    }
    """
    BINDINGS = [
        ("ctrl+c", "quit", ""),
        ("ctrl+l", "clear_log", ""),
    ]

    def __init__(self):
        super().__init__()
        self.config = _load_config()
        self.model = self.config.get("model", "qwen3.6")
        self.harness = self.config.get("harness_mode", "claude_compat")
        self.start_time = time.time()
        self._reset_messages()
        from clients import get_client
        self.client = get_client(self.config)

    def _reset_messages(self):
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    def compose(self):
        yield ChatLog(id="chat-log", markup=True, highlight=False)
        yield InputArea()
        yield StatusBar("", id="status-bar")

    def on_mount(self):
        log = self.query_one(ChatLog)
        log.write(render_banner_mascot())
        log.write("")
        cwd = str(Path.cwd())
        if len(cwd) > 60:
            cwd = "..." + cwd[-57:]
        harness_label = "darkclaude-native" if self.harness == "darkclaude_native" else "claude-compat"
        log.write(f" [#6a6a6a]version  [/]  [#b095d5]{VERSION}[/]")
        log.write(f" [#6a6a6a]model    [/]  [#5a8a98]{self.model}[/]")
        log.write(f" [#6a6a6a]server   [/]  [#5a8a98]{self.config.get('base_url','http://localhost:8080')}[/]")
        log.write(f" [#6a6a6a]cwd      [/]  [#e0e0e0]{cwd}[/]")
        log.write(f" [#6a6a6a]phase    [/]  [#b095d5]A6 stabilization[/]")
        log.write(f" [#6a6a6a]harness  [/]  [#b095d5]{harness_label}[/]")
        log.write("")
        log.write(" [#6a6a6a]Type /help for commands.  Ctrl+C to exit.[/]")
        log.write("")
        self._update_status_bar()
        self.query_one(Input).focus()

    def _update_status_bar(self, thinking=""):
        status = self.query_one(StatusBar)
        elapsed = int(time.time() - self.start_time)
        m, s = divmod(elapsed, 60)
        thinking_part = f"  [#b095d5]{thinking}[/]" if thinking else ""
        left = (
            f"[#5a8a98]{self.model}[/] "
            f"[#6a6a6a]\u00b7[/] [#b095d5]Phase A6 stabilization[/]  "
            f"[#6a6a6a]\u00b7[/]  [#6a6a6a]Ctrl+Y: copy mode[/]"
            f"{thinking_part}"
        )
        right = f"[#5a8a98]\u23f1 {m}m {s:02d}s[/]"
        status.update_status(f"{left}    {right}")

    def on_input_submitted(self, event):
        text = event.value.strip()
        if not text:
            return
        event.input.clear()
        if text.startswith("/"):
            self._handle_command(text)
        else:
            log = self.query_one(ChatLog)
            # 全幅背景: アプリ幅に合わせてスペースを埋める
            w = self.size.width - 3
            padded = f"{text:<{w}}"
            log.write(f"[on #1a1a1a][bold white]\u25b8 [/][#7a7a7a]{padded}[/]")
            self.run_worker(self._ai_turn(text), exclusive=True)

    async def _ai_turn(self, user_input):
        from tools.registry import TOOL_SCHEMAS, dispatch
        import random
        log = self.query_one(ChatLog)
        verbs = ["Thinking","Cooking","Brewing","Pondering","\u63a8\u8ad6\u4e2d","\u89e3\u6790\u4e2d","\u601d\u7d22\u4e2d"]
        verb = random.choice(verbs)
        log.write(f"[#b095d5]\u273b {verb}...[/]")
        self._update_status_bar(thinking=f"\u273b {verb}")
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
                    for line in content.split("\\n"):
                        log.write(f"[#e0e0e0]{line if line else ' '}[/]")
                    log.write("")
                    break
                for tc in tool_calls:
                    name = tc.get("function", {}).get("name", "")
                    args = tc.get("function", {}).get("arguments", {})
                    key_val = ""
                    for k in ("path", "command", "pattern", "query"):
                        if k in args:
                            key_val = str(args[k])
                            break
                    if not key_val and args:
                        key_val = str(next(iter(args.values())))
                    if len(key_val) > 47:
                        key_val = key_val[:44] + "..."
                    key_val = key_val.replace("\\n", "\u21b5")
                    t_start = time.time()
                    log.write(f"[#5a8a98]\u25cf {name}({key_val})[/]")
                    result = await asyncio.to_thread(dispatch, name, args)
                    elapsed_t = time.time() - t_start
                    summary = result[:100].replace("\\n", " ")
                    if len(result) > 100:
                        summary += "..."
                    color = "#a85050" if result.startswith("ERROR:") else "#5a8a98"
                    log.write(f"  [{color}]\u23bf {summary}[/] [#6a6a6a]({elapsed_t:.1f}s)[/]")
                    self.messages.append({"role": "tool", "content": result, "name": name})
        except Exception as e:
            log.write(f"[bold #a85050]ERROR:[/] {e}")
        finally:
            self._update_status_bar()

    def _handle_command(self, cmd):
        log = self.query_one(ChatLog)
        if cmd in ("/exit", "/quit", "/bye"):
            self.exit()
        elif cmd == "/clear":
            self.action_clear_log()
            self._reset_messages()
        elif cmd == "/help":
            log.write("[#6a6a6a]  /exit /clear /help[/]")
        else:
            log.write(f"[#a85050]  unknown:[/] {cmd}")

    def action_clear_log(self):
        self.query_one(ChatLog).clear()


def run():
    DarkClaudeApp().run()

if __name__ == "__main__":
    run()
'''

with open("tui/textual_app.py", "w", encoding="utf-8") as f:
    f.write(code)
print("done")
