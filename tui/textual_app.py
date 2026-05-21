# -*- coding: utf-8 -*-
import sys, asyncio, json, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from textual.app import App, ComposeResult
from textual.widgets import Input, RichLog, Static
from textual.containers import Horizontal, Vertical

_CONFIG_PATH = Path(__file__).parent.parent / "config.json"
VERSION = "v0.9-beta"
SYSTEM_PROMPT = '## あなたの役割\n\nあなたは DarkClaude です。ローカルで動く Qwen3 ベースの\nコーディングエージェントで、プロジェクト内のコード読解・編集・\nシェルコマンド実行を通じてユーザーを補佐します。\n作業対象は常に Windows 上のローカルプロジェクトです。\n\n## 振る舞い指針\n\n### 応答言語\n\nユーザーが日本語で質問した場合は日本語で、英語の場合は英語で応答すること。\nユーザーの使用言語と異なる言語で応答してはならない。\n\n### 応答スタイル\n\n応答は技術文書として読みやすい文体で書くこと。絵文字、過剰な装飾、\nマーケティング調の表現（"🌟", "Pro Tip", "Final Note",\n"**Key Features**" のような見出し装飾、感嘆符の多用）は使わない。\n箇条書きは要素が 3 つ以上ある時のみ使い、それ未満なら散文で書く。\n\n### プロジェクト固有名詞の取り扱い\n\nプロジェクトのファイル名、関数名、コマンド、設定項目等の固有名詞は、\n実ファイル（read_file / glob で確認したもの）または前のターンで\nユーザーが明示したものだけを使用すること。\n未確認の名詞を「もっともらしい推測」で生成してはならない。\n不明な場合は、その旨を明示するか、ツール呼び出しで確認してから応答すること。\n\n### ツール結果の参照\n\nツール呼び出しの結果は必ず応答に反映すること。\nツール結果を取得した後に、結果と無関係な汎用的な説明・分析・推奨に\n流れてはならない。\n\nユーザーが「X を Y して」と依頼した場合、X に関する一般的解説ではなく\nY を実行することを優先する。「ファイル編集」「ツール実行」が主旨であれば、\nまずツールを呼び出し、その後に必要最小限の説明を加える。\n\n### 空のツール結果の扱い\n\nツールが空の出力（"" や "(no output)"）を返した場合、それは正常な結果である\n可能性が高い。「曖昧な結果」として複数の可能性を列挙する反応は避けること。\nツール定義に従って、空出力は「正常終了かつ出力なし」と解釈すること。\n（例: Start-Sleep、mkdir、rm 等は出力なしで成功する）\n\n## ツール呼び出しのプロトコル\n\nツール呼び出しは必ず tool_calls フィールドで行うこと。\nmessage content に JSON 形式のツール呼び出しテキストを出力しては\nならない（実ツール呼び出しが発火せず、ユーザーは混乱する）。\n\nツールを呼び出すべきタイミングでは、応答テキストを返すのではなく\n必ずツールを呼び出すこと。\n\n## ファイル編集の手順\n\nファイルを編集する前に read_file で該当箇所を確認すること。\n既存内容を確認せずに編集を行ってはならない。\n\n既存ファイルへの局所的な変更（関数 1 つの修正、docstring 追加、\n数行の追加・変更など）には str_replace を使うこと。\nwrite_file はファイル全体を上書きするため、局所編集に使うと\n意図しない損失が発生する。\n\nwrite_file は以下の場合のみ使うこと:\n- 新規ファイルの作成\n- 明示的にファイル全体を置き換える場合\n\nstr_replace で old_str が見つからない、または複数箇所に存在する\n場合はエラーとなる。read_file で対象箇所を確認し、十分なコンテキストを\n含めた old_str を指定すること。\n\n## ツール実行失敗時の振る舞い\n\nツール実行が失敗した場合、原因を断定的に推測してユーザーに\n報告してはならない。\n\n複数の可能性が考えられる場合は、確証のない推測を「対処法」として\n箇条書きにせず、状況を簡潔に説明してユーザーまたは追加のツール\n呼び出しによる切り分けを促すこと。\n\n特に bash の timeout エラーでは、複数の可能性（時間不足、\nネットワーク、プロセス停止、コマンド誤り等）があるため、\nこれらを断定的に列挙せず、まずは timeout を増やして再試行する\n選択肢を提案すること。\n\n---\n\n## ユーザー承認について\n\nwrite_file と bash の実行前に、ユーザーは承認プロンプトを受け取る。\nユーザーが Deny / Ctrl+C を選んだ場合、tool_result は\n"USER_DENIED: ..." で始まる文字列になる。\n\nUSER_DENIED が返ってきた場合:\n- これはユーザーの意思による拒否であり、システムエラーやファイル権限の\n  問題ではない。原因を推測しない。\n- 「ファイルが読み取り専用」「権限がない」「パターンが原因」などの\n  技術的推測を一切しない。\n- ユーザーに何をしたいか確認するか、別のアプローチ（読み取り、別パス、\n  別コマンドなど）を提案する。\n- USER_DENIED は過去の一度のツール実行に対する拒否であり、その後の\n  ユーザーの新しい指示には影響しない。ユーザーが改めて同じ種類の\n  操作を指示した場合は、躊躇せずツールを呼び出して再度承認を求めること。\n  過去の拒否履歴を根拠にツール呼び出しをスキップしてはならない。\n  各ツール呼び出しは独立した判断であり、承認プロンプトはユーザーの\n  意思を確認する正しい手段である。'

BANNER_LINES = [' ██████╗  █████╗ ██████╗ ██╗  ██╗ ██████╗██╗      █████╗ ██╗   ██╗██████╗ ███████╗', ' ██╔══██╗██╔══██╗██╔══██╗██║ ██╔╝██╔════╝██║     ██╔══██╗██║   ██║██╔══██╗██╔════╝', ' ██║  ██║███████║██████╔╝█████╔╝ ██║     ██║     ███████║██║   ██║██║  ██║█████╗', ' ██║  ██║██╔══██║██╔══██╗██╔═██╗ ██║     ██║     ██╔══██║██║   ██║██║  ██║██╔══╝', ' ██████╔╝██║  ██║██║  ██║██║  ██╗╚██████╗███████╗██║  ██║╚██████╔╝███████╗', ' ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚══════╝']
MASCOT_LINES = ['   █        █', '   ██      ██', '  ██▀██████▀██', '    ██▄ ████ ▄██', '  ████████████████', '  ████████████', '   █ █    █ █']

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
    return "\n".join(lines)


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
        yield Static("─" * 400, classes="sep")
        with Horizontal():
            yield Static("▸ ", classes="prompt-char")
            yield Input(placeholder="", id="input-area")
        yield Static("─" * 400, classes="sep")


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
            f"[#6a6a6a]·[/] [#b095d5]Phase A6 stabilization[/]  "
            f"[#6a6a6a]·[/]  [#6a6a6a]Ctrl+Y: copy mode[/]"
            f"{thinking_part}"
        )
        right = f"[#5a8a98]⏱ {m}m {s:02d}s[/]"
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
            log.write(f"[on #1a1a1a][bold white]▸ [/][#7a7a7a]{padded}[/]")
            self.run_worker(self._ai_turn(text), exclusive=True)

    async def _ai_turn(self, user_input):
        from tools.registry import TOOL_SCHEMAS, dispatch
        import random
        log = self.query_one(ChatLog)
        verbs = ["Thinking","Cooking","Brewing","Pondering","推論中","解析中","思索中"]
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
                    for line in content.split("\n"):
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
                    key_val = key_val.replace("\n", "↵")
                    t_start = time.time()
                    log.write(f"[#5a8a98]● {name}({key_val})[/]")
                    result = await asyncio.to_thread(dispatch, name, args)
                    elapsed_t = time.time() - t_start
                    summary = result[:100].replace("\n", " ")
                    if len(result) > 100:
                        summary += "..."
                    color = "#a85050" if result.startswith("ERROR:") else "#5a8a98"
                    log.write(f"  [{color}]⎿ {summary}[/] [#6a6a6a]({elapsed_t:.1f}s)[/]")
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
