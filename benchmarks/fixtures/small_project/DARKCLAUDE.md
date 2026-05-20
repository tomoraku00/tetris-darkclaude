# small_project

DarkClaude TUI アプリの縮小版。ファイル構造要約タスク (T01) 用。

## ファイル構成

- main.py: エントリポイント
- prompts.py: システムプロンプト
- clients/: LLM クライアント
- tools/: ツール実装 (read_file, write_file, bash, glob, str_replace)
- tui/: TUI 実装 (app.py, chat.py, output.py 等)

## 作業方針

glob で全体像を把握してから read_file で主要ファイルを確認する。
推測でファイルを読まない。

## 例

ユーザー: このプロジェクトのファイル構造を要約して
応答:
glob(**/*.py) → ファイル一覧確認
read_file(main.py) → エントリポイント確認
要約: main.py がエントリポイント。tui/ に TUI 実装、tools/ にツール群、clients/ に LLM クライアント。
