"""OutputBuffer — FormattedText フラグメントを蓄積してスタイル付き出力を実現する。"""
import threading
from prompt_toolkit.formatted_text import FormattedText


class OutputBuffer:
    """スレッドセーフなスタイル付き出力バッファ。

    FormattedTextControl のコールバック (get_formatted_text) から参照される。
    Window への参照を持ち、append/clear 時に自動スクロールを制御する。
    """

    def __init__(self) -> None:
        self._fragments: list[tuple[str, str]] = []
        self._lock = threading.Lock()
        self.window = None    # app.py で Window 生成後に設定
        self.auto_scroll = True

    # ---- 読み出し (UI スレッドから呼ばれる) ----

    def get_formatted_text(self) -> FormattedText:
        with self._lock:
            return FormattedText(list(self._fragments))

    # ---- 書き込み (background thread からも呼ばれる) ----

    def append(self, text: str) -> None:
        """プレーンテキストを class:output スタイルで追加する。"""
        with self._lock:
            self._fragments.append(("class:output", text))
        self._try_scroll()

    def append_fragments(self, fragments: list[tuple[str, str]]) -> None:
        """スタイル付きフラグメントリストをそのまま追加する。"""
        with self._lock:
            self._fragments.extend(fragments)
        self._try_scroll()

    def clear(self) -> None:
        with self._lock:
            self._fragments.clear()
        if self.window is not None:
            self.window.vertical_scroll = 0

    # ---- 内部 ----

    def get_plain_lines(self) -> list[str]:
        """コピーモード用: プレーンテキストを行リストで返す。"""
        with self._lock:
            text = "".join(t for _, t in self._fragments)
        return text.split("\n")

    def _try_scroll(self) -> None:
        """auto_scroll が有効なら出力末尾にジャンプする。"""
        if self.auto_scroll and self.window is not None:
            self.window.vertical_scroll = 999999
