# DarkClaude 変更履歴

各バージョンで何ができるようになったかの記録。

---

## v0.5（完了）

**目標**: Plan モードの追加。LLM が実装せず手順を提示するだけのモードを `/plan` で切り替える。

### 新規
- `/plan` コマンド: Plan モードのトグル（揮発、再起動でリセット）
- Plan モード ON 時の挙動:
  - REPL プロンプトを `User [PLAN] > ` に切り替え
  - system prompt を Plan モード専用に切り替え（実装禁止・計画提示のみ指示）
  - `chat_turn()` 内で system メッセージを messages 先頭に挿入してから `ollama.chat()` へ送信
- ツール呼び出しの 2 層防御:
  - LLM 層: system prompt で write_file / bash を禁止と明示
  - コード層: `dispatch()` に `plan_mode: bool = False` 引数を追加し、`write_file` / `bash` 呼び出しを `ERROR: <name> は Plan モード中は使用できません。/plan で通常モードに戻してください。` でブロック
- 起動バナーのコマンド一覧に `/plan` を追加
- `main.py` のバージョン表示を v0.5 に更新

### 動作確認済み
- 起動バナーに `v0.5` と表示される
- `/plan` でプロンプトが `User [PLAN] > ` に変化
- Plan モード中に「README.md を書き換えて」→ LLM が write_file を呼ばず計画だけ提示
- Plan モード中に強制 write_file → `ERROR: write_file は Plan モード中は使用できません。...`
- Plan モード中に bash 実行依頼 → LLM が拒否 or コード側で ERROR ブロック
- Plan モード中に「main.py を読んで」→ read_file が正常動作
- 再度 `/plan` でプロンプトが `User > ` に戻る
- 再起動後は通常モードで起動（揮発確認）

### 制限事項
- Plan モードのまま再起動しても引き継がれない（揮発が仕様）
- Plan モード中も `/model` / `/setmodel` は使用可能（制限対象外）

---

## v0.4（完了）

**目標**: grep / glob ツールの追加。LLM がプロジェクト内を自分で検索・参照できるようにする。

### 新規
- `tools/grep.py`: 正規表現による内容検索ツール
  - パラメータ: `pattern`（必須）, `path`（省略時 `.`）, `include`（glob フィルタ）, `case_insensitive`（省略時 false）
  - 出力: `パス:行番号:マッチ行` 形式、最大 100 件・1 行 200 文字・合計 4000 文字でキャップ
  - バイナリファイルは先頭 1KB の null バイト判定でスキップ
- `tools/glob.py`: glob パターンによるファイルパス検索ツール
  - パラメータ: `pattern`（必須）, `path`（省略時 `.`）
  - 出力: マッチしたパスの一覧（PROJECT_ROOT 相対）、最大 200 件・4000 文字でキャップ
- 両ツール共通: 除外ディレクトリ固定（`.git`, `node_modules`, `__pycache__`, `.venv`, `venv`, `.mypy_cache`, `.pytest_cache`）、隠しディレクトリ（`.` 始まり）をスキップ
- `tools/registry.py` に grep / glob を登録
- `main.py` のバージョン表示を v0.4 に更新

### 動作確認済み
- `main.py に def が何個ある？` → `main.py:XX:def ...` 形式で列挙される
- `tools/ 配下の .py で SCHEMA を検索して` → include フィルタで tools/*.py に絞られた結果
- `error を大文字小文字無視で探して` → case_insensitive マッチ
- 存在しない文字列を検索 → `(no matches)`
- `プロジェクト内の .py ファイルを列挙して` → 全 .py ファイルのパス一覧
- `../Windows を検索して` → `ERROR: path outside project root: ...`

### 制限事項
- `.gitignore` の内容に基づく除外は未対応（固定除外ディレクトリのみ）
- ディレクトリを対象とした glob（ファイルのみ返す仕様）

---

## v0.3.3（完了）

**目標**: モデル設定の永続化コマンド追加。

### 新規
- `save_config(config: dict)`: config.json に設定を書き込むヘルパー（`ensure_ascii=False` / `indent=2`）
- `/setmodel <name>` コマンド: セッションのモデルを変更し、config.json の `"model"` フィールドも同時に書き換える
  - 存在しないモデル名の場合は警告を出して config.json を変更しない
  - 引数なしの場合は使い方を表示
- 起動バナーのコマンド一覧に `/setmodel <name>` を追加
- バージョン表示を v0.3.3 に更新

### /model と /setmodel の使い分け
| コマンド | セッション | config.json |
|---|---|---|
| `/model <name>` | 変更 | 変更しない（揮発）|
| `/setmodel <name>` | 変更 | 書き換える（永続）|

### 動作確認済み
- `/setmodel qwen2.5-coder:7b` → config.json の model が書き換わり次回起動時も維持される
- `/setmodel nonexistent:latest` → 警告表示、config.json は変更されない
- `/setmodel`（引数なし）→ `Usage: /setmodel <name>` を表示

---

## v0.3.2（完了）

**目標**: モデル切り替え機能の追加。

### 新規
- `config.json`（プロジェクトルート）: `{"model": "qwen3:8b"}` を起動時読み込みのデフォルト設定ファイルとして新規作成
- `load_config()`: config.json を読んでモデル名を返す。ファイルなし/読み込みエラー時は `qwen3:8b` にフォールバック
- `get_installed_models()`: `ollama.list()` でインストール済みモデル名を取得するヘルパー
- `/models` コマンド: `ollama list` の出力をそのまま表示
- `/model <name>` コマンド: モデルをセッション内で切り替え。存在しない名前なら警告してインストール済み一覧を表示
- `/model`（引数なし）: 現在のモデル名を表示
- `chat_turn()` に `model: str` 引数を追加し、ハードコード `"qwen3:8b"` を排除
- 起動バナーに `/models` / `/model <name>` のヘルプを追加、バージョン表示を v0.3.2 に更新

### 動作確認項目
- 起動時に config.json のモデルが読み込まれ `Model: qwen3:8b` と表示される
- `/models` でインストール済み一覧が表示される
- `/model qwen2.5-coder:7b` で切り替え後、次のターンから新モデルで応答される
- `/model nonexistent` で警告＋インストール済み一覧が表示される
- `/model` 単体で現在のモデル名が表示される

### 制限事項
- モデル切り替えは現在のセッション限り（config.json への書き戻しは未対応）

---

## v0.3.1（完了）

**目標**: bash ツールの日本語出力文字化け修正。

### 原因（2層構造）

1. **データ層**: PowerShell が cp932（Shift-JIS）でコンソール出力するのに Python 側が `encoding="utf-8"` で読もうとしていた → `run()` の戻り値が破損
2. **表示層**: `sys.stdout.encoding = cp932` の端末で Python が UTF-8 文字列を print する際に garble が発生

### 修正

**`tools/bash.py`**: コマンド実行前に PowerShell の出力エンコーディングを UTF-8 に強制するプリアンブルを自動付与（対処案2採用）。

```
$OutputEncoding = [System.Text.Encoding]::UTF8; [Console]::OutputEncoding = [System.Text.Encoding]::UTF8;
```

cp932 をハードコードする案（対処案1）より、プリアンブル方式（対処案2）を採用。理由: システムロケール依存を排除でき、非日本語環境でも動作する。

**`main.py`**: 起動時に `sys.stdout.reconfigure(encoding="utf-8")` を追加。REPL の表示（ツール結果プレビュー等）が cp932 端末でも文字化けしない。

### 動作確認済み
- `run()` の戻り値を UTF-8 ファイルに書き出すと正しい日本語が記録される（データ層修正の確認）
- REPL の `[result]` 表示に日本語が正しく出力される

---

## v0.3（完了）

**目標**: bash 実行ツールの追加。

### 新規
- `tools/bash.py`: PowerShell をサブプロセスで実行する `bash` ツール
- シェル自動検出: `pwsh.exe` → `powershell.exe` の優先順で検出
- CWD: `PROJECT_ROOT` 固定（外部ディレクトリへの飛び出し防止）
- タイムアウト: 30 秒（超過時 `ERROR: timeout after 30s`）
- 出力上限: 4000 文字（超過時末尾を切り詰めて `...[truncated]` を付記）
- 危険コマンドブロックリスト: `Stop-Computer`, `Restart-Computer`, `Format-Volume`, `Clear-Disk`, ルートへの `Remove-Item -Recurse -Force`
- `tools/registry.py` に bash を登録
- `main.py` のバージョン表示を v0.3 に更新

### 動作確認済み
- `Get-ChildItem` でプロジェクトルートのファイル一覧取得
- `python --version` でバージョン確認
- exit code 1 → `ERROR: exit code 1` を正しく返す
- `Stop-Computer` → `ERROR: blocked command: ...` を正しく返す

### 制限事項（v0.4 以降で拡張予定）
- grep / glob による複数ファイル検索不可（v0.4 で追加）
- 権限承認なし（v0.6 で本格実装）
- bash/cmd は非対応（PowerShell のみ）

---

## v0.2（完了）

**目標**: ツール基盤の構築と read_file / write_file の実装。

### 新規
- `tools/` パッケージ構造（`__init__.py`, `registry.py`, `read_file.py`, `write_file.py`）
- Ollama tool calling 対応（OpenAI 互換 function 形式のスキーマ）
- `read_file` ツール（プロジェクトルート配下のテキストファイル読み込み）
- `write_file` ツール（プロジェクトルート配下にテキストファイル書き込み、親ディレクトリ自動作成）
- パス安全性: `is_relative_to(PROJECT_ROOT)` でルート配下のみ許可
- エンコーディング: `encoding="utf-8"` 明示で Windows の cp932 事故防止
- エラー応答フォーマット: `ERROR: <理由>` 形式の文字列で統一
- `main.py` 構造改善: `chat_turn` 関数化、`if __name__ == "__main__"` パターン、ASCII アートを純 ASCII 文字化

### 動作確認済み
- README.md の読み込みと内容要約
- test.txt の書き込み（プロジェクト内）
- `/exit` `/quit` `/bye` でのクリーン終了
- LLM が制約理解の上でプロジェクト外パスを試行回避（二重防御として機能）
- パス安全性のコード自体は実装済み（直接呼び出しテスト可能）

### 既知の挙動
- qwen3:8b は安全側に倒すため、明らかに「外のファイル」と分かるパスはツールを呼ばずに自己拒否することがある
- コード側のパス制限は別途機能しているため二重の防御線として成立

### 制限事項（v0.3 以降で解消予定）
- bash 実行不可
- grep / glob による複数ファイル検索不可

---

## v0.1（完了）

**目標**: Ollama と会話できる最小エージェント

### 新規
- ASCII アートロゴ表示
- Ollama (qwen3:8b) との会話 REPL
- 会話履歴の保持（インメモリ）
- `/exit` `/quit` `/bye` での終了
- Ctrl+C による安全終了

### 動作確認済み
- Windows 11 + Python 3.14 + Ollama 0.24 + qwen3:8b で起動・対話成立

### 制限事項（v0.2 で解消済み）
- ツール使用なし（チャットのみ）
- ファイル操作不可
- bash 実行不可

---

## Step 0（完了）

**目標**: プロジェクト基盤

### 新規
- プロジェクトディレクトリ構造
  - `README.md`
  - `main.py`（雛形）
  - `requirements.txt`（依存: ollama）
  - `.gitignore`
  - `tools/`（空フォルダ、v0.2 で使う）
- 開発環境構築
  - Ollama インストール
  - Qwen2.5-Coder 7B モデル取得
  - Qwen3 8B モデル取得
  - VS Code + Cline 拡張セットアップ
  - Cline ↔ Ollama 接続確認

---

## 設定変更履歴

### Cline 設定
- Auto-approve: Read project files, Edit project files, Execute safe commands, MCP servers
- Model Context Window: 32768
- Request Timeout: 30000ms（必要に応じて延長）

### Ollama 設定
- デフォルト Keep-alive: 5分（未変更）
- Context length: モデル既定（qwen3:8b は 40K）

### v0.2 までの開発体制
- 設計議論: Claude.ai（チャット）
- 実装: Cline + qwen2.5-coder:7b / qwen3:8b
- v0.3 以降は Claude Code (Max プラン) を主担当に変更予定（開発期間短縮のため）
