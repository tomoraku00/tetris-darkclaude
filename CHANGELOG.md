# DarkClaude 変更履歴

各バージョンで何ができるようになったかの記録。

---

## v0.8（完了）

**目標**: LoRA 訓練環境の構築。v0.7 で収集した会話ログを ChatML 形式に変換し、Unsloth + 4bit QLoRA で Qwen3 モデルを訓練・評価するパイプラインを `training/` サブディレクトリに整備する。

### 新規
- `training/prepare.py`: 会話ログ（`data/conversations/*.jsonl`）→ ChatML JSONL 変換スクリプト
  - `--input` / `--output` オプション（省略時はデフォルトパス）
  - thinking_ratio: `<think>` ブロックを含む LLM 呼び出しの割合を標準出力に表示
  - データが空でも正常終了（メッセージを表示して 0 件で完了）
- `training/train.py`: Unsloth 4bit QLoRA 訓練スクリプト
  - `--config`（YAML）、`--data`（ローカル JSONL）、`--hf-dataset`（HF データセット）、`--max-steps` オプション
  - run_id: タイムスタンプ + 6 桁 hex、`output/<run_id>/` に保存
  - VRAM ログ: モデルロード後・訓練開始前・empty_cache 後・訓練終了後を出力
  - 訓練後に LoRA adapter と meta.json を `output/<run_id>/adapter/` に保存
  - Windows 環境対応: `dataloader_num_workers=0`、`device_map={"": 0}`（bnb4bit CPU dispatch 回避）
- `training/eval.py`: 訓練前後の応答比較評価スクリプト
  - `--adapter`（LoRA adapter パス）、`--out`（出力ディレクトリ）
  - `eval_set/prompts.jsonl` を読み込み、ベースモデル / 訓練後モデルの応答を比較
  - `eval_results/<timestamp>_<run_id>.md` に Markdown 出力（手動採点欄付き）
- `training/deploy.py`: Ollama デプロイ スケルトン（v0.9 で実装）
- `training/configs/lora_default.yaml`: LoRA 訓練設定（model, lora, training セクション）
- `training/eval_set/prompts.jsonl`: 評価プロンプト 3 件（code-read / code-write / general）
- `training/requirements.txt`: 訓練側依存（unsloth, transformers, trl, datasets, accelerate, bitsandbytes, pyyaml 等）
- `training/README.md`: セットアップ手順・パイプライン実行・VRAM 注意・トラブルシューティング

### 変更
- `training/` ディレクトリを `nanoclaude/` 配下に新設（本体 Python 3.14 と隔離した Python 3.12 専用 venv で動作）

### Windows 環境での既知問題と対処（重要）
| 問題 | 原因 | 対処 |
|---|---|---|
| `STATUS_ACCESS_VIOLATION (0xC0000005)` | Unsloth 2026.5.2 + torch 2.11: `from unsloth import` より前に `import datasets` が必要 | `import datasets` を最初に置く（import 順序固定） |
| SSL 証明書エラー（HF ダウンロード失敗） | Windows の OS 証明書ストアと certifi の乖離 | `truststore` パッケージをインストールして `truststore.inject_into_ssl()` を呼ぶ |
| hf_transfer SSL bypass（ダウンロードが 0% でハング） | `unsloth/dataprep/synthetic.py` が `HF_HUB_ENABLE_HF_TRANSFER=1` を強制設定 | `pip uninstall hf_transfer -y` で削除 |
| hf_xet SSL bypass（大ファイルが 0% でハング） | hf-xet は独自 SSL スタックで truststore を bypass | `HF_HUB_DISABLE_XET=1` + `pip uninstall hf_xet -y` |
| `ValueError: Some modules dispatched on CPU` | Unsloth デフォルトの `device_map="sequential"` が bnb4bit と競合 | `device_map={"": 0}` を `FastLanguageModel.from_pretrained` に指定 |
| fused CE loss VRAM OOM（Qwen3-8B のみ） | RTX 4060 8GB に対して Qwen3-8B 4bit が ~7GB を占有し、first forward pass 後に free VRAM ≈ 0 | `unsloth_zoo/fused_losses/cross_entropy_loss.py` の `target_gb <= 1e-9` 分岐で `raise` → `target_gb = 0.01` に変更（venv パッチ） |

### 動作確認済み
- `python prepare.py` → データ空でも正常完了、thinking_ratio 表示
- `python train.py --config configs/lora_default.yaml --hf-dataset tatsu-lab/alpaca --hf-max-samples 1000 --max-steps 100`
  → 100 steps 完了（Qwen3-4B 4bit: ~2分15秒、VRAM peak ~3.75GB）
  → `output/<run_id>/adapter/` に LoRA adapter 保存
- `python eval.py --adapter output/<run_id>/adapter`
  → `eval_results/<timestamp>_<run_id>.md` に比較 Markdown 出力
- `python -c "import training.deploy"` → `deploy import OK`

### 制限事項
- **Qwen3-8B の 100-step サニティチェックは RTX 4060 8GB では実用的でない**: VRAM 消費 ~7GB + 訓練オーバーヘッドで 1 step が 50〜130s に達し、100 steps に約 2〜3 時間かかる。サニティチェックは Qwen3-4B（~3.5GB VRAM、1.3s/step）で実施した。本番訓練での 8B 使用は設定変更後に試行すること
- `unsloth_zoo` の fused CE loss パッチは venv ローカル変更のため `pip install --upgrade unsloth` で上書きされる
- eval_set の本番プロンプト 20 件はユーザーが手書きで追加する（現在 3 件）
- deploy.py は v0.9 で実装予定
- **v0.9 着手前にベースモデル選定議論が必要**: Qwen3-8B は RTX 4060 8GB では訓練不可と判明。本体 Ollama の `qwen3:8b` との整合性（4B で訓練したモデルを 8B ベースの本体と整合させるか、ハードウェアを増強するか等）をユーザーと Claude.ai で議論してから v0.9 を進めること

---

## v0.7（完了）

**目標**: 軽量会話ログ収集。会話・ツール呼び出し・モデル応答をセッション単位で JSONL ファイルに保存し、v0.8 以降の LoRA 訓練データの土台を作る。

### 新規
- `session_log.py`: `SessionLog` クラスを新規追加
  - コンストラクタ: `enabled`, `base_dir`, `dc_version`, `model`, `plan_mode`, `think_mode`, `system_prompt` を受け取り、`session_id = secrets.token_hex(4)`（8桁 hex）を生成
  - 状態管理: `_enabled` / `_dead` の 2 フラグ（ファイル書き込み失敗時は `_dead = True` にしてサイレントに無視）
  - ファイル: `data/conversations/YYYYMMDD-HHMMSS_<session_id>.jsonl` を追記モード・UTF-8 で保存
  - タイムスタンプ: UTC ミリ秒精度（`2026-05-17T10:23:45.123Z` 形式）
  - `json.dumps(ensure_ascii=False, default=str)` で非シリアライズ可能オブジェクトも安全に文字列化
  - イベントメソッド: `session_start()`, `user_message()`, `llm_call()`, `tool_call()`, `approval()`, `tool_result()`, `assistant_message()`, `close()`
  - 制御メソッド: `toggle()`, `set_enabled()`, `update_context(plan_mode, think_mode)`
- `/logging` コマンド: セッション内のログ収集トグル（揮発）
  - ON 時: `ログ収集: ON (data/conversations/...jsonl)` でファイルパスも表示
  - OFF 時: `ログ収集: OFF`
- `data/conversations/` ディレクトリ: SessionLog が初回書き込み時に `mkdir(parents=True, exist_ok=True)` で自動作成
- `.gitignore` に `data/` を追記（ログファイルをコミット除外）

### 変更
- `_build_system_prompt(plan_mode, think_mode) -> str` ヘルパーを追加（chat_turn() 内のインライン構築を切り出し）
- `chat_turn()` に `session_log: SessionLog | None = None` 引数を追加
  - ログポイント: user_message → llm_call（while ループ毎）→ tool_call → approval → tool_result → assistant_message
  - `llm_call` の `latency_ms`: `time.monotonic()` で ollama.chat() 前後を計測
  - `assistant_message` の `total_latency_ms`: `turn_start` からターン終了まで
- `main()` で SessionLog を初期化し、ロゴ表示前に `session_start()` を呼び出し
- `/plan` / `/think` 変更時に `session_log.update_context()` を呼び出してコンテキスト同期
- 終了時に `session_log.close(reason)`: `/exit /quit /bye` → `"user_exit"`, Ctrl+C/D → `"ctrl_c"`
- コマンドヘルプに `/logging` を追加
- バナー表示を v0.7 に更新

### ログイベント形式（1行1JSON）
| type | 主要フィールド |
|---|---|
| `session_start` | dc_version, model, plan_mode, think_mode, logging_enabled, system_prompt, session_id |
| `user_message` | content |
| `llm_call` | request_messages, response (msg dict), latency_ms, plan_mode, think_mode |
| `tool_call` | tool, args |
| `approval` | tool, args, decision |
| `tool_result` | tool, args, content, is_user_denied |
| `assistant_message` | content, total_latency_ms |
| `session_end` | reason, session_id |

### 動作確認済み
- バナーに `v0.7` と表示
- 起動直後に `data/conversations/YYYYMMDD-HHMMSS_<id>.jsonl` が自動生成
- 1 ターン（質問 → 応答）後、JSONL に session_start → user_message → llm_call → assistant_message → session_end（終了時）が記録
- ツール使用ターンで tool_call / approval / tool_result が記録
- `/logging` で OFF → ファイルに何も追記されなくなる
- `/logging` で ON に戻す → 既存ファイルに追記再開
- `/plan` ON/OFF で log の plan_mode フィールドが更新（llm_call イベントで確認）
- `/think hide` で log の think_mode フィールドが更新
- Ctrl+C 終了 → JSONL に `reason: "ctrl_c"` の session_end が記録
- `/exit` 終了 → JSONL に `reason: "user_exit"` の session_end が記録
- `data/` が `.gitignore` に含まれ `git status` で追跡されない

### 制限事項
- ログ収集の有効/無効は揮発（再起動で `DEFAULT_LOGGING_ENABLED = True` に戻る）
- 良否マーキング（LoRA 品質フィルタ）は v0.8 で実装
- ログファイルのローテーション・サイズ上限なし（暫定）
- `llm_call` の `response` フィールドは msg dict（Pydantic モデルは `default=str` でフォールバック）

---

## v0.6.5（完了）

**目標**: qwen3 思考モードの 3 値制御。show（表示）/ hide（非表示）/ off（思考なし）を `/think` コマンドで切り替え、config.json に永続化する。

### 新規
- `main.py` に `DEFAULT_THINK_MODE = "show"` / `THINK_MODES = ("show", "hide", "off")` 定数を追加
- `ThinkStripper` クラスを追加（`<think>...</think>` ブロックをチャンク単位で除去）
- `/think` コマンドを追加
  - 引数なし: show → hide → off → show の巡回
  - `/think show|hide|off`: 直接指定
  - 不正引数: `ERROR: invalid think mode '...'. Use: show | hide | off`
  - 変更時に config.json 即時更新 + `Think mode: HIDE (was SHOW)` 形式で確認表示
- `chat_turn()` に `think_mode: str = "show"` 引数を追加

### 変更
- **off モード**: system prompt 末尾に `\n\n/no_think` を追記 + `ollama.chat(think=False)` を渡す
  - `TypeError` の場合（旧 ollama-python）: `[warn]` ログを 1 回だけ表示してリトライ（`_think_fallback_warned` グローバルフラグで制御）
- **hide モード**: 最終テキスト応答を `ThinkStripper.feed() + flush()` でフィルタしてから表示
- **show モード**: 既存動作のまま（`<think>` ブロックをそのまま表示）
- プロンプト表示: `User >` / `User [HIDE] > ` / `User [NOTHINK] > ` で現モードを表記（Plan モードとの組み合わせ: `User [PLAN] [NOTHINK] > ` 等）
- config.json に `think_mode` キーを追加、起動時にキーが無ければサイレントマイグレーション（警告なし）
- 不正値が config.json に入っていた場合は `[warn]` + `"show"` にフォールバック + 上書き
- `/setmodel` や起動時モデルフォールバックの `save_config()` 呼び出しに `think_mode` を含めるよう更新
- バナー表示を v0.6.5 に更新

### 動作確認済み
- バナーに `v0.6.5` と表示
- 起動直後 config に `think_mode` キーなし → "show" が書き込まれる、警告なし、プロンプトは `User > `
- `/think` 巡回（show → hide → off → show）と直接指定（`/think hide`）
- 不正引数（`/think foobar`）→ ERROR 表示、モード変更なし
- show モードで質問 → `<think>` ブロックが画面に出る
- hide モードで質問 → `<think>` ブロックが画面に出ない、答えだけ出る
- off モードで質問 → `<think>` ブロックがそもそも生成されない、応答時間が速い
- hide モードで複雑な質問 → `<think>` 部分が表示されず本体応答だけ表示
- off モード + Plan モード → `User [PLAN] [NOTHINK] > ` 表示
- 再起動 → 直前のモードが config.json から復元
- config.json の `think_mode` を "invalid" に書き換えて起動 → 警告ログ + "show" にフォールバック + 上書き

### 制限事項
- `<think>` ブロックのたたみ込み表示（「思考中 12s を展開」）→ TUI 化前提、将来検討
- タスク種別による自動 think on/off 判定 → 未実装

---

## v0.6.4（完了）

**目標**: 複数行ペースト対応と手動改行（`\ + Enter`）の追加。REPL の入力受付を `input()` から prompt_toolkit の `PromptSession` に置き換え、複数行入力・入力履歴・行内編集を実現する。

### 変更
- `main.py` に prompt_toolkit インポートを追加（`PromptSession`、`InMemoryHistory`、`KeyBindings`）
  - prompt_toolkit は v0.6.1 の questionary 依存として既にインストール済み、新規依存なし
- メインの `input()` を `PromptSession.prompt()` に置き換え
  - `InMemoryHistory` による入力履歴（↑↓ で過去の入力を辿れる、揮発）
  - ←→、Home/End、Backspace、Ctrl+A/E などの行内編集が効く
  - bracketed paste mode 対応（ターミナルからのペーストで改行が送信されず入力欄に保持される）
  - 複数行入力中の続き行に `prompt_continuation = "... "` を表示
- `\ + Enter` による手動改行の実装（`KeyBindings` で Enter キーを上書き）
  - 行末が `\` の場合: `\` を削除して `\n` を挿入し入力継続
  - それ以外の場合: 通常通り送信（`validate_and_handle()`）
- `except` 節に `EOFError` を追加して Ctrl+D によるクリーン終了をサポート
- バナー表示を v0.6.4 に更新

### 動作確認済み
- バナーに `v0.6.4` と表示
- 通常の 1 行入力 + Enter → 既存通り送信
- 複数行テキストのクリップボードからのペースト → 全行が入力欄に保持され、Enter で全体が 1 メッセージとして送信
- 行末に `\` を打って Enter → 送信されず `\` が消えて改行が入る、次の行頭に `... ` が出る
- `\` 改行を複数行続けた後 Enter → 全体が 1 メッセージとして送信（改行は `\n` として保持）
- コマンド（`/exit` `/plan` `/model` `/models`）→ 既存通り動作
- ↑ キー → 直前の入力が呼び出される、↓ で戻れる
- ←→ Home End Backspace → 行内で自由にカーソル移動・編集
- Ctrl+C → `KeyboardInterrupt`、既存通りクリーン終了
- Ctrl+D → `EOFError`、クリーン終了
- 複数行ペーストを含む write_file 指示 → 既存の承認 UI（questionary）と競合なし

### 制限事項（将来検討）
- 入力履歴の永続化（`FileHistory`）→ セッション内のみの揮発
- コマンド補完（`/exit` `/plan` 等のタブ補完）→ 未対応
- 入力欄の色付け・スタイル → 将来 TUI 化と合わせて検討

---

## v0.6.3（完了）

**目標**: 削除済みモデルのフォールバック。config.json に記録されているモデルが Ollama から削除されていた場合、起動時に検出して `qwen3:8b` に自動フォールバックする。

### 変更
- `main.py` に `FALLBACK_MODEL = "qwen3:8b"` 定数を追加（フォールバック先の単一箇所管理）
- `main.py` 起動シーケンスにモデル存在チェックを追加（ASCII アート表示直後、`Model:` 表示前）
  - `ollama.list()` を直接呼んでインストール済みモデル一覧を取得（例外を適切に捕捉するため `get_installed_models()` ではなく直接呼び出し）
  - config のモデルが一覧に存在すれば何もしない（通常起動）
  - 存在しない場合: `[warn]` 2 行を表示し `FALLBACK_MODEL` へフォールバック + `config.json` を更新
  - `FALLBACK_MODEL` も存在しない場合: `ERROR:` メッセージと `ollama pull qwen3:8b` 案内を表示し `sys.exit(1)` で起動拒否
  - Ollama 未起動等で例外が発生した場合: チェックをスキップして起動継続（最初のチャットで Ollama 接続エラーが出る、既存挙動を維持）
- バナー表示を v0.6.3 に更新

### 動作確認済み
- バナーに `v0.6.3` と表示
- 通常起動（config に `qwen3:8b`、Ollama にも存在）→ 警告なし、通常起動
- config に存在しないモデル名を設定して起動 → `[warn]` 2 行表示、`qwen3:8b` にフォールバック、`config.json` が書き換わる
- フォールバック後そのままチャット → `qwen3:8b` で正常動作
- Ollama を停止して起動 → 警告なし（チェックをスキップ）、起動継続
- `qwen3:8b` を削除した状態で非存在モデルを config に設定して起動 → `ERROR:` メッセージと `ollama pull` 案内で起動拒否

### 制限事項
- 起動時のチェックのみ（実行中にモデルが削除されても検出しない）
- フォールバック先は `FALLBACK_MODEL = "qwen3:8b"` 固定（変更する場合は定数を編集）

---

## v0.6.2（完了）

**目標**: Deny 時のフィードバック文言 polish。LLM が "ERROR: ..." を「システムエラー」と誤解釈し、「ファイルが読み取り専用」等の技術的推測をしてしまう問題を修正する。

### 変更
- `main.py`: `_SYSTEM_PROMPT` 定数を新規追加
  - ユーザー承認の仕組みと `USER_DENIED: ...` マーカーの意味を LLM に伝えるシステムプロンプト
  - 「原因を推測しない」「技術的推測をしない」「別アプローチを提案するか確認する」の 3 点を明示
  - 通常モード・Plan モードの両方で常に先頭に挿入する（Plan モード時は `_PLAN_SYSTEM_PROMPT + _SYSTEM_PROMPT` を連結）
- `main.py`: ユーザーが Deny / Ctrl+C を選んだ際の tool_result メッセージを変更
  - 旧: `"ERROR: ユーザーが承認を拒否しました"`
  - 新: `"USER_DENIED: あなた（ユーザー）がこのツールの実行を拒否しました。ファイル権限などシステムの問題ではありません。別のアプローチを提案するか、何をしたいか確認してください。"`
  - "ERROR" → "USER_DENIED:" マーカーに変更し、LLM がエラーとして扱わないようにする
- `main.py`: ログ表示を `-> denied by user` から `-> USER_DENIED` に変更（tool_result マーカーと表記を統一）
- `main.py`: 不正引数時（path/command が空）の tool_result を `"ERROR: ツールの引数が不正です（path または command が空）"` に修正（"ユーザーが拒否" という不正確な文言を削除）
- バナー表示を v0.6.2 に更新

### 動作確認済み
- バナーに `v0.6.2` と表示
- write_file で Deny → `[tool] ... -> USER_DENIED`、LLM が「ファイル権限の問題」等の推測をしない
- bash で Deny → 同上
- Ctrl+C で承認キャンセル → USER_DENIED 文言、誤解釈なし
- Allow once / Always allow の通常フロー → v0.6.1 と同じ挙動（回帰なし）
- Plan モード中の write_file → 既存の _PLAN_BLOCKED メッセージのまま、影響なし
- read_file / grep / glob → 承認プロンプトなし（影響なし）

### 制限事項（v0.6.x 以降で段階追加予定）
- パターンマッチ許可（git *, npm test * 等のワイルドカード）は未対応
- 理由付き deny（拒否時にユーザーがフィードバックテキストを入力して LLM に渡す機能）は未対応
- 承認リストの永続化（config.json 書き込み）は未対応

---

## v0.6.1（完了）

**目標**: 承認メニューを矢印キー TUI 化。questionary.select() による上下選択 + Enter 確定に置き換える。

### 変更
- `tools/approval.py`: 番号入力ループを `questionary.select()` に差し替え
  - ヘッダー（Tool / Path / Content / Size / Command）の表示フォーマットは v0.6 と同一
  - 選択肢ラベルも v0.6 と同一（"Allow once" / "Always allow ..." / "Deny"）
  - Ctrl+C → `None` 返却または `KeyboardInterrupt` 、いずれも "deny" にマップ
  - 無効入力の概念がなくなり（メニュー固定）、再プロンプトループを削除
- `requirements.txt` に `questionary>=2.0.0` 追加
- `README.md` に依存パッケージのインストール手順を追記
- バナー表示を v0.6.1 に更新

---

## v0.6（完了）

**目標**: 権限承認システムの追加。write_file / bash の実行直前にユーザーに承認を求め、「1回許可 / 常に許可 / 拒否」を選ばせる。

### 新規
- `tools/approval.py`: 承認 UI の実装
  - `request_approval(tool_name, args) -> "allow_once" | "always_allow" | "deny"`
  - write_file: Path / Content（先頭80文字、改行→`\n`）/ Size を表示
  - bash: Command を表示
  - 「1. Allow once / 2. Always allow ... / 3. Deny」メニュー
  - 無効入力は再プロンプト、Ctrl+C / EOFError は deny 扱い（REPL は継続）
- `main.py` 承認ゲート（`chat_turn()` 内、dispatch 直前）
  - 対象: write_file / bash（Plan モード OFF の時のみ）
  - read_file / grep / glob は対象外（副作用なし）
  - Plan モード ON の時は承認スキップ（dispatch で既にブロックされる）
  - 「常に許可」の粒度: write_file はパス単位、bash はコマンド完全一致
- セッション状態（揮発、再起動でリセット）
  - `allowed_write_paths: set[str]`、`allowed_bash_commands: set[str]` を `main()` のローカル変数として保持
  - `chat_turn()` の引数として受け渡し、グローバル変数は使わない
  - set は mutable なので `always_allow` 追加が `main()` 側にも反映される
- 2 層防御の整理: 承認ゲート（ユーザー判断）→ Plan モードブロック（コード判断）→ dispatch
- バナー表示を v0.6 に更新

### 動作確認済み
- バナーに `v0.6` と表示
- write_file に approval needed プロンプトが出る（Path / Content / Size 表示）
- 1 選択 → 実行成功、同パスの次回は再度プロンプト
- 2 選択 → 実行成功、同パスの以降はプロンプトなしで即実行（許可済みセット）
- 3 選択 → `[tool] ... -> denied by user`、LLM に `ERROR: ユーザーが承認を拒否しました` が返る
- bash も同様の承認 UI（Command 表示、Always allow '<command>'）
- 同コマンド文字列で 2 選択後は以降プロンプトなし
- 別コマンドは別許可が必要
- Ctrl+C → deny 扱い、REPL は継続
- 無効入力（4, yes, 空）→ 再プロンプト
- Plan モード中は承認プロンプトなし、既存の Plan ブロックが効く
- read_file / grep / glob はプロンプトなし
- 再起動後は許可リセット（揮発確認）

### 制限事項（v0.6.x 以降で段階追加予定）
- パターンマッチ許可（git *, npm test * 等のワイルドカード）は未対応
- 理由付き deny（拒否時に LLM へのフィードバック）は未対応
- 許可リストの永続化（config.json 書き込み）は未対応

---

## v0.5.3.1（完了）

**目標**: ThinkingIndicator の日本語動詞リストをテック寄りに調整。

### 変更
- `_THINKING_VERBS` の日本語項目を差し替え
  - 削除: 醸造中, 煮込み中（料理寄り、DarkClaude の雰囲気にそぐわない）
  - 追加: 推論中, 解析中, 演算中, 思索中, 分析中
  - 保持: 思考中, 考え中
- 英語項目は変更なし（7 語）
- 最終リスト: 14 語（英語 7 + 日本語 7）
- バナー表示を v0.5.3.1 に更新

---

## v0.5.3（完了）

**目標**: 作業時間表示の追加（Claude Code 風）。LLM 推論中のスピナー・ツール経過時間・ターン合計時間を表示する。

### 新規
- `ThinkingIndicator` コンテキストマネージャ（`main.py`）
  - `ollama.chat()` 呼び出しを `with ThinkingIndicator():` で囲む
  - `threading.Thread(daemon=True)` で 1 秒ごとに `✻ <動詞> for Ns` を同じ行に上書き表示
  - 動詞リスト（11 語）: Thinking / Cooking / Brewing / Cogitating / Crunching / Pondering / Simmering / 考え中 / 思考中 / 醸造中 / 煮込み中
  - 動詞は `__enter__` 時に 1 度だけランダム選択し、スレッドと共有（ターン内で動詞が変わらない）
  - `__exit__` 時にスレッドを停止し `\r` + スペース + `\r` で行をクリア
- ツール実行時の経過時間表示
  - `time.monotonic()` で dispatch 前後を計測
  - `[tool]` 行の末尾に `[N.Ns]` を追記（例: `[tool] read_file({'path': 'main.py'}) [0.2s]`）
- ターン完了時の合計時間表示
  - 最終応答の直後に `  (合計 N.Ns)` を出力
  - ターン開始（`chat_turn()` 入口）から最終テキスト応答まで計測
- `main.py` のバージョン表示を v0.5.3 に更新

### 動作確認済み
- バナーに `v0.5.3` と表示
- 単純な質問 → `✻ X for Ns` が動的更新、応答後クリア、`(合計 N.Ns)` 表示
- ツール使用 → `[tool] name(args) [N.Ns]` 形式で経過時間表示
- 複数ターンで異なる動詞が出現（ランダム性確認）

---

## v0.5.2（完了）

**目標**: grep ツールが単一ファイル指定を受け付けるよう拡張。Unix の `grep pat file.py` と同じ感覚で使えるようにする。

### 変更
- `tools/grep.py` の `run()` を file/dir 二分岐構造に書き直し
  - `path` がファイル → そのファイル 1 件だけを検索
  - `path` がディレクトリ → 既存通り再帰走査（互換性維持）
  - `path` が存在しない → `ERROR: not found: <path>`（メッセージも統一）
- 検索ロジックを `_search_file(file, regex, matches)` ヘルパーに抽出し重複を排除
- SCHEMA の `path` 引数の説明を「ファイルまたはディレクトリ」に更新
- `main.py` のバージョン表示を v0.5.2 に更新

### 動作確認済み
- `grep('def ', path='main.py')` → `main.py:N:def ...` 形式で def 行が返る
- `grep('def run', include='tools/*.py')` → 既存通りディレクトリ走査が動く（互換性）
- `grep('test', path='foo.py')` → `ERROR: not found: foo.py`
- `grep('test', path='../Windows')` → `ERROR: path outside project root: ...`

---

## v0.5.1（完了）

**目標**: ツール呼び出しの無限リトライ抑制。LLM が同じエラーを繰り返し呼び続ける挙動を 2 段の安全機構でブロックする。

### 新規
- **① 同一呼び出し連続検出**: 直前 3 回が同じ `(tool_name, args)` の組なら 4 回目以降をブロック
  - `collections.deque(maxlen=3)` で直近の呼び出しを追跡
  - args は `json.dumps(sort_keys=True)` で dict 順序の揺れを吸収して比較
  - ブロック時は `ERROR: 同じツール呼び出しが3回繰り返されました。...` を tool_result として LLM に返す
- **② ターン内総呼び出し上限（25回）**: 1 ターンの tool_call 総数が 25 回を超えたらブロックしてターン終了
  - ブロック時は `ERROR: このターンの tool_call 回数が上限（25回）に達しました。...` を返し、REPL ループを中断
  - ターミナルに `[安全機構] ターン内 tool_call 上限（25回）に達しました。` を表示
- 両カウンタはユーザーの新しい入力ごとにリセット（`chat_turn()` 内で揮発保持）
- `main.py` のバージョン表示を v0.5.1 に更新

### 動作確認済み
- 起動バナーに `v0.5.1` と表示される
- 存在しないファイルを繰り返し読ませると 3 回目まで `ERROR: file not found`、4 回目以降は連続検出 ERROR でブロックされてループ収束
- 通常の複数ツール連続使用（grep → read_file → 別ファイル read_file）は検出に引っかからず正常動作
- Plan モード中の read_file 連続でも本機構が正常に動く

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
