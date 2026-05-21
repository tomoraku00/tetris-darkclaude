code = r'''# -*- coding: utf-8 -*-
import sys, asyncio, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from textual.app import App, ComposeResult
from textual.widgets import Input, RichLog, Static

_CONFIG_PATH = Path(__file__).parent.parent / "config.json"

BANNER = """
 ██████╗  █████╗ ██████╗ ██╗  ██╗ ██████╗██╗      █████╗ ██╗   ██╗██████╗ ███████╗
 ██╔══██╗██╔══██╗██╔══██╗██║ ██╔╝██╔════╝██║     ██╔══██╗██║   ██║██╔══██╗██╔════╝
 ██║  ██║███████║██████╔╝█████╔╝ ██║     ██║     ███████║██║   ██║██║  ██║█████╗
 ██║  ██║██╔══██║██╔══██╗██╔═██╗ ██║     ██║     ██╔══██║██║   ██║██║  ██║██╔══╝
 ██████╔╝██║  ██║██║  ██║██║  ██╗╚██████╗███████╗██║  ██║╚██████╔╝██████╔╝███████╗
 ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚══════╝"""

def _load_config():
    try:
        return json.loads(_CONFIG_PATH.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}

class StatusBar(Static):
    DEFAULT_CSS = """
    StatusBar {
        height: 1;
        background: #0a0a0f;
        color: #666677;
        padding: 0 1;
        border-top: solid #5c0030;
    }
    """
    def update_status(self, text: str) -> None:
        self.update(text)

class ChatLog(RichLog):
    DEFAULT_CSS = """
    ChatLog {
        height: 1fr;
        background: #0a0a0f;
        color: #e8e8f0;
        border: none;
        padding: 0 1;
        scrollbar-gutter: stable;
        scrollbar-color: #5c0030 #0a0a0f;
    }
    """

class DarkClaudeApp(App):
    CSS = """
    Screen {
        background: #0a0a0f;
        layout: vertical;
    }
    #input-area {
        height: 3;
        border: solid #5c0030;
        background: #0a0a0f;
        color: #e8e8f0;
        padding: 0 1;
    }
    #input-area:focus {
        border: solid #cc0066;
    }
    """
    BINDINGS = [
        ("ctrl+c", "quit", "終了"),
        ("ctrl+l", "clear_log", "クリア"),
    ]

    def __init__(self):
        super().__init__()
        self.config = _load_config()
        self.model = self.config.get("model", "default")
        self.messages = []
        from clients import get_client
        self.client = get_client(self.config)

    def compose(self) -> ComposeResult:
        yield ChatLog(id="chat-log", markup=True, highlight=True)
        yield Input(placeholder="▸ ", id="input-area")
        yield StatusBar("", id="status-bar")

    def on_mount(self) -> None:
        log = self.query_one(ChatLog)
        log.write(f"[bold #ff0080]{BANNER}[/]")
        log.write("")
        log.write(f"  [#666677]version[/]    [#b266ff]v0.9-beta-final[/]")
        log.write(f"  [#666677]model  [/]    [#00d9ff]{self.model}[/]")
        log.write(f"  [#666677]server [/]    [#e8e8f0]{self.config.get('base_url','http://localhost:8080')}[/]")
        log.write(f"  [#666677]phase  [/]    [#b266ff]Textual B[/]")
        log.write("")
        self._update_status_bar()
        self.query_one(Input).focus()

    def _update_status_bar(self, thinking: bool = False) -> None:
        status = self.query_one(StatusBar)
        if thinking:
            status.update_status("[#ff0080]✻ 推論中...[/]")
        else:
            status.update_status(
                "[#00ff88]●[/] llama-server  "
                "[#666677]|[/]  [#666677]VRAM free:[/] [#00d9ff]1564 MiB[/]  "
                "[#666677]|[/]  [#666677]model:[/] [#b266ff]Qwen3.6-35B[/]  "
                "[#666677]|[/]  [#666677]ctx:[/] [#e8e8f0]--[/]"
            )

    def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        if not text:
            return
        event.input.clear()
        if text.startswith("/"):
            self._handle_command(text)
        else:
            log = self.query_one(ChatLog)
            log.write(f"[bold #b266ff]▸[/] [#b266ff]{text}[/]")
            self.run_worker(self._ai_turn(text), exclusive=True)

    async def _ai_turn(self, user_input: str) -> None:
        from tools.registry import TOOL_SCHEMAS, dispatch
        log = self.query_one(ChatLog)
        self._update_status_bar(thinking=True)
        self.messages.append({"role": "user", "content": user_input})
        tool_call_count = 0
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
                    log.write(f"[#e8e8f0]{content}[/]")
                    log.write("")
                    break
                for tc in tool_calls:
                    name = tc.get("function", {}).get("name", "")
                    args = tc.get("function", {}).get("arguments", {})
                    args_str = ", ".join(f"{k}={repr(v)[:40]}" for k, v in args.items())
                    log.write(f"[#00d9ff]  ❯ {name}({args_str})[/]")
                    result = await asyncio.to_thread(dispatch, name, args)
                    log.write(f"[#888899]    {result[:200]}[/]")
                    self.messages.append({"role": "tool", "content": result, "name": name})
                    tool_call_count += 1
        except Exception as e:
            log.write(f"[bold #ff0040]ERROR:[/] {e}")
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
            log.write("[#666677]  /exit /clear /help[/]")
        else:
            log.write(f"[#ff0040]  unknown:[/] {cmd}")

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
