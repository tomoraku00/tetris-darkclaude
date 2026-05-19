"""アプリ内コピーモード (tmux 風 / OSC 52 クリップボード)"""
import sys
from base64 import b64encode
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.filters import Condition


class CopyMode:
    """Ctrl+Y でコピーモードに入り、矢印+v で範囲選択 → y/Enter でコピー。

    マウスホイールスクロール (mouse_support=True) を維持しつつ
    テキスト選択 → クリップボードコピーを可能にする。
    visual cursor のハイライトはステータスライン経由でフィードバック。
    """

    def __init__(self) -> None:
        self.is_active = False
        self.cursor_row = 0
        self.cursor_col = 0
        self.selection_start: tuple[int, int] | None = None
        self.output_lines: list[str] = []

    def enter(self, output_lines: list[str]) -> None:
        self.is_active = True
        self.output_lines = output_lines
        self.cursor_row = max(0, len(output_lines) - 1)
        self.cursor_col = 0
        self.selection_start = None

    def exit(self) -> None:
        self.is_active = False
        self.selection_start = None

    def get_status_hint(self) -> str:
        """ステータスラインに表示するコピーモード情報を返す。"""
        n = len(self.output_lines)
        row_info = f"L{self.cursor_row + 1}/{n}" if n else "L0"
        if self.selection_start is not None:
            sr, sc = self.selection_start
            return f"[COPY] {row_info} col:{self.cursor_col}  sel from L{sr+1}  y/Enter=copy  Esc=cancel"
        return f"[COPY] {row_info} col:{self.cursor_col}  v=select  y=copy  Esc=cancel"

    def get_selected_text(self) -> str:
        if self.selection_start is None:
            # 選択なし: カーソル行を返す
            if 0 <= self.cursor_row < len(self.output_lines):
                return self.output_lines[self.cursor_row]
            return ""

        sr, sc = self.selection_start
        er, ec = self.cursor_row, self.cursor_col

        # 順序を正規化
        if (sr, sc) > (er, ec):
            sr, sc, er, ec = er, ec, sr, sc

        lines = self.output_lines
        if sr >= len(lines):
            return ""

        if sr == er:
            return lines[sr][sc : ec + 1]

        parts = [lines[sr][sc:] if sr < len(lines) else ""]
        for row in range(sr + 1, er):
            parts.append(lines[row] if row < len(lines) else "")
        if er < len(lines):
            parts.append(lines[er][: ec + 1])
        return "\n".join(parts)

    def copy_to_clipboard(self, text: str) -> None:
        """OSC 52 シーケンスでクリップボードへ書き込む (クロスプラットフォーム)。"""
        if not text:
            return
        b64 = b64encode(text.encode("utf-8")).decode("ascii")
        seq = f"\x1b]52;c;{b64}\x07"
        try:
            out = getattr(sys, "__stdout__", sys.stdout)
            out.write(seq)
            out.flush()
        except Exception:
            pass

    def _move_cursor(self, dr: int, dc: int) -> None:
        n = len(self.output_lines)
        self.cursor_row = max(0, min(n - 1, self.cursor_row + dr))
        if self.output_lines and 0 <= self.cursor_row < n:
            max_col = max(0, len(self.output_lines[self.cursor_row]) - 1)
            self.cursor_col = max(0, min(max_col, self.cursor_col + dc))

    def make_keybindings(self) -> KeyBindings:
        kb = KeyBindings()
        active = Condition(lambda: self.is_active)

        @kb.add("up", filter=active, eager=True)
        def _(event):
            self._move_cursor(-1, 0)
            event.app.invalidate()

        @kb.add("down", filter=active, eager=True)
        def _(event):
            self._move_cursor(1, 0)
            event.app.invalidate()

        @kb.add("left", filter=active, eager=True)
        def _(event):
            self._move_cursor(0, -1)
            event.app.invalidate()

        @kb.add("right", filter=active, eager=True)
        def _(event):
            self._move_cursor(0, 1)
            event.app.invalidate()

        @kb.add("s-up", filter=active, eager=True)
        def _(event):
            if self.selection_start is None:
                self.selection_start = (self.cursor_row, self.cursor_col)
            self._move_cursor(-1, 0)
            event.app.invalidate()

        @kb.add("s-down", filter=active, eager=True)
        def _(event):
            if self.selection_start is None:
                self.selection_start = (self.cursor_row, self.cursor_col)
            self._move_cursor(1, 0)
            event.app.invalidate()

        @kb.add("s-left", filter=active, eager=True)
        def _(event):
            if self.selection_start is None:
                self.selection_start = (self.cursor_row, self.cursor_col)
            self._move_cursor(0, -1)
            event.app.invalidate()

        @kb.add("s-right", filter=active, eager=True)
        def _(event):
            if self.selection_start is None:
                self.selection_start = (self.cursor_row, self.cursor_col)
            self._move_cursor(0, 1)
            event.app.invalidate()

        @kb.add("v", filter=active, eager=True)
        def _(event):
            if self.selection_start is None:
                self.selection_start = (self.cursor_row, self.cursor_col)
            else:
                self.selection_start = None
            event.app.invalidate()

        @kb.add("enter", filter=active, eager=True)
        @kb.add("y", filter=active, eager=True)
        def _(event):
            text = self.get_selected_text()
            if text:
                self.copy_to_clipboard(text)
            self.exit()
            event.app.invalidate()

        @kb.add("escape", filter=active, eager=True)
        @kb.add("q", filter=active, eager=True)
        def _(event):
            self.exit()
            event.app.invalidate()

        return kb
