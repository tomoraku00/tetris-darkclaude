# -*- coding: utf-8 -*-
"""DarkClaude Textual TUI - Phase B スケルトン"""
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, RichLog, Static


class StatusBar(Static):
    DEFAULT_CSS = """
    StatusBar {
        height: 1;
        background: #1e1e2e;
        color: #6c7086;
        padding: 0 1;
    }
    """
    def update_status(self, vram_free: int = 0, model: str = "") -> None:
        self.update(f"VRAM free: {vram_free} MiB | Model: {model} | Context: --")


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

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield ChatLog(id="chat-log", markup=True, highlight=True)
        yield Input(placeholder="メッセージを入力... (Ctrl+C で終了)", id="input-area")
        yield StatusBar(id="status-bar")

    def on_mount(self) -> None:
        log = self.query_one(ChatLog)
        log.write("[bold green]DarkClaude[/] Phase B Textual TUI - 起動完了")
        self.query_one(StatusBar).update_status(vram_free=1564, model="Qwen3.6-35B-A3B")
        self.query_one(Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        if not text:
            return
        log = self.query_one(ChatLog)
        log.write(f"[bold cyan]You:[/] {text}")
        event.input.clear()
        if text.startswith("/"):
            self._handle_command(text)
        else:
            log.write("[bold yellow]Assistant:[/] (AI 接続前のスタブ)")

    def _handle_command(self, cmd: str) -> None:
        log = self.query_one(ChatLog)
        if cmd in ("/exit", "/quit", "/bye"):
            self.exit()
        elif cmd == "/clear":
            self.action_clear_log()
        else:
            log.write(f"[red]Unknown command:[/] {cmd}")

    def action_clear_log(self) -> None:
        self.query_one(ChatLog).clear()


def run() -> None:
    DarkClaudeApp().run()


if __name__ == "__main__":
    run()
