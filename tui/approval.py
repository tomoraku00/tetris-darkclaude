"""承認 Dialog (prompt_toolkit ネイティブ実装、v0.9-beta)"""
import asyncio

from prompt_toolkit.filters import Condition
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import ConditionalContainer, Window
from prompt_toolkit.layout.controls import FormattedTextControl


class ApprovalDialog:
    """ツール承認用 in-TUI Dialog。questionary を置き換える。

    使い方:
        dialog = ApprovalDialog()
        # Layout に dialog.make_container() を組み込む
        # KeyBindings に dialog.make_keybindings() をマージする
        # ツール承認時:
        result_idx = await dialog.show(title, command, description, emphasis)
        # 0=Yes(once), 1=Yes(always), 2=No
    """

    _OPTIONS = [
        "Yes",
        "Yes, and always allow access to {emphasis} from this project",
        "No",
    ]

    def __init__(self) -> None:
        self.is_active = False
        self.section_title = ""
        self.command_text = ""
        self.description = ""
        self.emphasis_text = ""
        self.selected_index = 0
        self._future: asyncio.Future | None = None

    # ---- 公開 API ----

    async def show(
        self,
        section_title: str,
        command_text: str,
        description: str = "",
        emphasis: str = "",
    ) -> int:
        """Dialog を表示し、選択結果 (0/1/2) を返す。"""
        self.section_title = section_title
        self.command_text = command_text
        self.description = description
        self.emphasis_text = emphasis
        self.selected_index = 0
        self.is_active = True
        loop = asyncio.get_event_loop()
        self._future = loop.create_future()
        return await self._future

    # ---- Layout / KeyBindings ----

    def make_container(self) -> ConditionalContainer:
        return ConditionalContainer(
            content=Window(
                FormattedTextControl(self._get_content),
                wrap_lines=False,
            ),
            filter=Condition(lambda: self.is_active),
        )

    def make_keybindings(self) -> KeyBindings:
        kb = KeyBindings()
        active = Condition(lambda: self.is_active)

        @kb.add("up", filter=active)
        def _up(event):
            self.selected_index = max(0, self.selected_index - 1)
            event.app.invalidate()

        @kb.add("down", filter=active)
        def _down(event):
            self.selected_index = min(len(self._OPTIONS) - 1, self.selected_index + 1)
            event.app.invalidate()

        @kb.add("enter", filter=active)
        def _enter(event):
            self._resolve(self.selected_index)
            event.app.invalidate()

        @kb.add("1", filter=active)
        def _key1(event):
            self._resolve(0)
            event.app.invalidate()

        @kb.add("2", filter=active)
        def _key2(event):
            self._resolve(1)
            event.app.invalidate()

        @kb.add("3", filter=active)
        def _key3(event):
            self._resolve(2)
            event.app.invalidate()

        @kb.add("escape", filter=active)
        def _esc(event):
            self._resolve(2)  # No 扱い
            event.app.invalidate()

        return kb

    # ---- 内部 ----

    def _resolve(self, index: int) -> None:
        self.is_active = False
        if self._future and not self._future.done():
            self._future.set_result(index)

    def _get_content(self) -> FormattedText:
        if not self.is_active:
            return FormattedText([])

        width = 80
        parts: list[tuple[str, str]] = []

        # 上ライン
        parts.append(("class:section.divider", "─" * width + "\n"))
        # セクションヘッダー
        parts.append(("class:section.header", f" {self.section_title}\n\n"))
        # コマンド本文 (コードブロック背景)
        for line in self.command_text.split("\n"):
            parts.append(("class:code_block", line.ljust(width) + "\n"))
        # 説明文
        if self.description:
            parts.append(("class:section.subhead", f"  {self.description}\n"))
        parts.append(("", "\n"))
        # 質問
        parts.append(("class:assistant", " Do you want to proceed?\n"))
        # 選択肢
        for i, opt_tmpl in enumerate(self._OPTIONS):
            is_sel = (i == self.selected_index)
            cursor = ("class:option.cursor", "> ") if is_sel else ("", "  ")
            opt_style = "class:option.selected" if is_sel else "class:option.unselected"
            parts.append(cursor)
            label = f"{i + 1}. "
            if i == 1 and self.emphasis_text:
                before, _, after = opt_tmpl.partition("{emphasis}")
                parts += [
                    (opt_style, label + before),
                    ("class:option.emphasis", self.emphasis_text),
                    (opt_style, after + "\n"),
                ]
            else:
                parts.append((opt_style, label + opt_tmpl + "\n"))

        parts.append(("", "\n"))
        # 下ライン
        parts.append(("class:section.divider", "─" * width + "\n"))
        # ヒント
        parts.append(("class:option.hint", " Esc to cancel  ·  1/2/3 to select directly\n"))

        return FormattedText(parts)


def decision_from_index(index: int) -> str:
    """選択肢インデックスを approval_fn の戻り値文字列に変換する。"""
    if index == 0:
        return "allow_once"
    elif index == 1:
        return "always_allow"
    else:
        return "deny"
