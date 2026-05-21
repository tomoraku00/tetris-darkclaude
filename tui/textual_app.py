# -*- coding: utf-8 -*-
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
"""DarkClaude Textual TUI - Phase B (AI 接続版)"""
import asyncio
import json
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Header, Input, RichLog, Static
from textual.worker import get_current_worker


_CONFIG_PATH = Path(__file__).parent.parent / "config.json"


def _load_config() -> dict:
    try:
        return json.loads(_CONFIG_PATH.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}


class StatusBar(Static):
    DEFAULT_CSS = """
    StatusBar {
        height: 1;
        background: #1e1e2e;
        color: #6c7086;
        padding: 0 1;
    }
    """
    def update_status(self, text: str) -> None:
        self.update(text)


class ChatLog(RichLog):
    DEFAULT_CSS = """
    ChatLog {
        height: 1fr;
        border: none;
        scrollbar-gutter: stable;
    }
    """


class DarkClaudeApp(App):
    CSS = """
    Screen { layout: vertical; }
    #input-area {
        height: 3;
        border: solid #89b4fa;
        padding: 0 1;
    }
    """
    BINDINGS = [
        ("ctrl+c", "quit", "終了"),
        ("ctrl+l", "clear_log", "クリア"),
    ]

    def __init__(self):
        super().__init__()
        config = _load_config()
        self.model = config.get("model", "default")
        self.base_url = config.get("base_url", "http://localhost:8080")
        self.messages = []
        from clients import get_client
        self.client = get_client(config)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield ChatLog(id="chat-log", markup=True, highlight=True)
        yield Input(placeholder="メッセージを入力... (Ctrl+C で終了)", id="input-area")
        yield StatusBar("VRAM free: 1564 MiB | Model: Qwen3.6-35B-A3B | Context: --", id="status-bar")

    def on_mount(self) -> None:
        log = self.query_one(ChatLog)
        log.write("[bold green]DarkClaude[/] Textual TUI Phase B - 起動完了")
        self.query_one(Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        if not text:
            return
        event.input.clear()
        if text.startswith("/"):
            self._handle_command(text)
        else:
            log = self.query_one(ChatLog)
            log.write(f"[bold cyan]You:[/] {text}")
            self.run_worker(self._ai_turn(text), exclusive=True)

    async def _ai_turn(self, user_input: str) -> None:
        log = self.query_one(ChatLog)
        status = self.query_one(StatusBar)
        status.update_status("推論中...")
        self.messages.append({"role": "user", "content": user_input})
        try:
            response = await asyncio.to_thread(
                self.client.chat,
                self.model,
                self.messages,
                [],  # tools なし (Phase B-1 はシンプルチャットから)
            )
            msg = response.get("message", {})
            content = msg.get("content", "")
            self.messages.append(msg)
            log.write(f"[bold yellow]Assistant:[/] {content}")
        except Exception as e:
            log.write(f"[bold red]ERROR:[/] {e}")
        finally:
            status.update_status("VRAM free: 1564 MiB | Model: Qwen3.6-35B-A3B | Context: --")

    def _handle_command(self, cmd: str) -> None:
        log = self.query_one(ChatLog)
        if cmd in ("/exit", "/quit", "/bye"):
            self.exit()
        elif cmd == "/clear":
            self.action_clear_log()
        elif cmd == "/help":
            log.write("[bold]コマンド:[/] /exit /clear /help")
        else:
            log.write(f"[red]Unknown command:[/] {cmd}")

    def action_clear_log(self) -> None:
        self.query_one(ChatLog).clear()
        self.messages.clear()


def run() -> None:
    DarkClaudeApp().run()


if __name__ == "__main__":
    run()
