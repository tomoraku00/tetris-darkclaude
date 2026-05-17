# DarkClaude

ローカル LLM（Ollama）で動く Claude Code クローン。
`shareAI-lab/learn-claude-code`（NanoClaude）の harness engineering 思想を踏襲。

**最終的なゴール**: 個別 PC で運用ログから自己学習する AI を作ること。
モデル本体を LoRA で訓練する仕組みを v0.x の主目標とする。

---

## このファイルの位置づけ

Claude Code がプロジェクトメモリとして自動参照する **基本情報の入口**。

詳細は分離してあるので、作業前に下記すべてに目を通すこと:

- `CLAUDE.md`（このファイル）: 環境・規約・現状ステータス
- `ROADMAP.md`: バージョン計画と将来検討アイデア
- `CHANGELOG.md`: 完了バージョンの履歴

---

## 設計思想

```
Harness = Tools + Knowledge + Observation + Action Interfaces + Permissions
```

エージェント = モデル + ハーネス。モデルは既に賢い。コードの役割はその手足を作ること。

ただし DarkClaude は harness 思想の **その先** を目指す:
モデル自身が運用データから学習し、使い込むほど本体能力が向上する仕組みを内蔵する。

### コアパターン

すべてのバージョンは下記の最小ループに機構を追加していく形で進化する:

```
User --> messages[] --> LLM --> response
                                  |
                        tool_calls あり?
                       /                \
                     yes                 no
                      |                   |
                execute tools        return text
                append results
                loop back -----> messages[]
```

---

## 現在のステータス

### 完了（v0.8 まで）
- **v0.1〜v0.3**: REPL、ツール基盤（read/write/bash）
- **v0.4**: grep / glob ツール
- **v0.5〜v0.5.3.1**: Plan モード、無限リトライ抑制、grep 単一ファイル対応、作業時間表示
- **v0.6**: 権限承認システム（write_file / bash の実行前に承認プロンプト）
  - `tools/approval.py`: `request_approval()` が 1回許可 / 常に許可 / 拒否 を返す
  - 許可状態は揮発（セッション内のみ、再起動でリセット）
- **v0.6.1〜v0.6.5**: 承認 TUI 化、deny メッセージ polish、モデルフォールバック、複数行ペースト、思考モード制御
  - `/think [show|hide|off]`: qwen3 の思考ブロック表示を 3 値で制御（config.json に永続化）
  - show=思考表示（既定）、hide=思考非表示・速度同等、off=思考無効・高速
- **v0.7**: 軽量会話ログ収集（LoRA 訓練データの土台）
  - `session_log.py`: SessionLog クラス（JSONL 追記、per-session ファイル、UTC タイムスタンプ）
  - `/logging`: セッション内ログ収集トグル（揮発）
  - ログイベント: session_start / user_message / llm_call / tool_call / approval / tool_result / assistant_message / session_end
  - `data/conversations/` に保存（.gitignore 除外済み）
- **v0.8**: LoRA 訓練環境構築（Unsloth + データ整形パイプライン）
  - `training/`: Python 3.12 専用 venv（本体 3.14 と完全隔離）
  - prepare.py / train.py / eval.py / deploy.py（スケルトン）
  - サニティチェック: Qwen3-4B 4bit で 100 steps、~2 分、VRAM ~3.5GB（RTX 4060）
  - **重要**: Qwen3-8B は RTX 4060 8GB では訓練オーバーヘッドが収まらず非実用（1 step ~60s）

### 次のステップ
- **v0.9**: 初回 LoRA 訓練 + 評価ループ + Ollama デプロイ

詳細は ROADMAP.md のバージョン計画表参照。

---

## 環境

- **OS**: Windows 11
- **Python**: 3.14.x
- **Ollama**: 0.24.0
- **メインモデル**: qwen3:8b（思考モードあり）
- **副次モデル**: qwen2.5-coder:7b（速度優先時）
- **ハードウェア**: Ryzen 7 5700G / RAM 32GB / RTX 4060 (VRAM 8GB)
  - VRAM 8GB は 7B モデルの QLoRA 訓練の現実的な上限
  - 訓練時は他の VRAM 使用を停止する必要あり

---

## コーディング規約

### 必須ルール

- **ファイル I/O は必ず `encoding="utf-8"` を明示**（Windows の cp932 文字化け事故防止）
- **パス安全性**: `PROJECT_ROOT = Path.cwd().resolve()` を基準に、その配下のみ許可。外部パスは `ERROR: path outside project root: <path>` を返して拒否
- 型ヒントを使う
- ツールは `tools/` パッケージに配置、`registry.py` で集約

### エラー応答フォーマット

ツールがエラーを返す時は文字列で `"ERROR: <理由>"` 形式。例:
- `ERROR: path outside project root: <path>`
- `ERROR: file not found: <path>`
- `ERROR: cannot decode as utf-8: <path>`

### ツールスキーマ（重要）

**Ollama の tool calling は OpenAI 互換の function 形式**。Anthropic API 形式 (`input_schema`) ではないので注意:

```python
SCHEMA = {
    "type": "function",
    "function": {
        "name": "tool_name",
        "description": "...",
        "parameters": {
            "type": "object",
            "properties": {...},
            "required": [...]
        }
    }
}
```

NanoClaude のサンプルコードは Anthropic API 前提なので、そのまま流用せず Ollama 形式に書き換えてから使うこと。

---

## モデル選択の注意

**DarkClaude 自身のテスト時（ツール動作確認・機能検証）は必ず qwen3:8b で実行すること。**

### 理由

qwen2.5-coder:7b は tool calling 出力が不安定で、tool_calls フィールドではなく content の JSON テキストとしてツール呼び出しを出力することがある。ツール実装のバグではなくモデル起因の失敗が混入し、原因の切り分けが困難になる。

### テスト手順

```
テスト前: /setmodel qwen3:8b
テスト実施（ツール動作確認・機能検証）
テスト後: 必要に応じて /setmodel qwen2.5-coder:7b で元に戻す
```

### モデル別 tool calling 安定性（現時点）

| モデル | tool calling | 備考 |
|---|---|---|
| qwen3:8b | 安定 | テスト・開発時の標準モデル |
| qwen2.5-coder:7b | 不安定 | 速度優先の会話用途に限定推奨 |
| deepseek-r1:7b | 未検証 | 詳細は ROADMAP.md 参照 |

---

## 運用で判明した観察記録

実際に動かして判明した制約・挙動の記録。設計判断の根拠として残す。

- **v0.8 で判明: Qwen3-8B 4bit QLoRA は RTX 4060 8GB では実用不可 (2026-05-18)**:
  - max_seq_length 1024、empty_cache、fused CE loss target_gb=0.001/0.01 を
    試したが、最良で 51s/step、50 step 以降 130s/step に悪化
  - Qwen3-4B に切り替えると 1.3s/step で即解決
  - 本番訓練は VRAM 8GB ハードウェア上では 4B が現実的、8B 訓練には
    16GB 以上の VRAM が必要
  - 結論: v0.9 以降のベースモデル選定議論が必要
    （本体 Ollama の qwen3:8b との整合性をどうするか）

- **v0.8 で観測: 訓練データに `<think>` が含まれないと reasoning が抑制される方向に動く (2026-05-18)**:
  - alpaca 1000 件、Qwen3-4B、100 step の軽い訓練でも
    訓練後モデルの `<think>` 内が空 `\n\n` に縮退した
  - v0.9 の reasoning ratio 75/25 混合戦略の設計根拠を強化する観察

- **v0.8 で踏んだ追加の Windows 罠 (2026-05-18)**（将来の同種エラー初動チェックリスト）:
  - HuggingFace SSL エラー → `pip install truststore` + `truststore.inject_into_ssl()` で
    Python の SSL に Windows OS 証明書ストアを注入して回避
  - `hf_transfer` が Python SSL を bypass → `pip uninstall hf_transfer -y` で削除必須
    （Unsloth が `HF_HUB_ENABLE_HF_TRANSFER=1` を import 時に強制設定するため env var では防げない）
  - `hf-xet` も独自 SSL スタックで truststore を bypass → `HF_HUB_DISABLE_XET=1` +
    `pip uninstall hf_xet -y` で対処
  - bnb4bit + CPU dispatch エラー → `device_map={"": 0}` を `FastLanguageModel.from_pretrained`
    に指定して GPU 固定（デフォルトの `device_map="sequential"` が競合）

- **v0.8 完了後判断: Qwen3-4B は DarkClaude の用途では性能不足 (2026-05-18)**:
  - 素のベースモデル評価（DarkClaude のシステムプロンプト + ツール環境込み、
    未訓練）を 2 課題で実施
  - 課題 1（コード読解 + ツール呼び出し連鎖）: read_file の結果を反映せず
    汎用的な「Ollama チャットボット紹介文」に流れた。プロジェクト固有名詞を
    複数ハルシネーション（DarkClaude → DarkC、Qwen3 → Llama3、
    /setmodel → /model）。日本語質問に英語で応答
  - 課題 2（ピンポイント編集）: ツール呼び出し JSON をメッセージ本文として
    出力（実ツール呼び出しが発火せず）。仮に発火していれば write_file で
    対象ファイル全体を docstring 1 つだけに置換していた（ファイル破壊リスク）。
    read_file による事前確認なし、ツール選択も誤り
  - 結論: 8B → 4B の段差はベンチマーク数値以上に大きく、エージェント用途では
    別モデルとして扱うべき。プロンプト調整では救えない構造的能力差

---

## ディレクトリ構造（目標）

```
darkclaude/
├── CLAUDE.md           # このファイル
├── ROADMAP.md          # バージョン計画と将来検討
├── CHANGELOG.md        # 完了バージョン履歴
├── README.md
├── config.json         # モデル設定（起動時読み込み）
├── main.py             # REPL エントリポイント
├── session_log.py      # 会話ログ収集（v0.7）
├── requirements.txt
├── .gitignore
├── tools/
│   ├── __init__.py
│   ├── registry.py     # TOOL_SCHEMAS と dispatch（Plan モードブロック含む）
│   ├── approval.py     # 承認 UI（v0.6）
│   ├── read_file.py    # v0.2
│   ├── write_file.py   # v0.2
│   ├── bash.py         # v0.3
│   ├── grep.py         # v0.4（単一ファイル対応済み）
│   └── glob.py         # v0.4
├── data/               # ★ v0.7 から使う（運用ログ蓄積場所）
│   └── conversations/  # JSONL ファイル群
└── training/           # ★ v0.8 から使う（LoRA 訓練関連）
    ├── prepare.py      # ログ → 学習データ変換
    ├── train.py        # Unsloth 訓練スクリプト
    └── eval.py         # 訓練前後の評価
```

---

## 重要な前提・制約

- **配布対象**: ローカル完結、外部 API 呼び出しなし（OpenAI / Anthropic 等のクラウド API は使用禁止）
- **学習機構の核は LoRA**: モデル本体を訓練して能力向上させるのが主目標（v0.7〜v0.9）
- **周辺機構（キャッシュ・RAG・スキル蓄積）は v1.x で後付け**: 元 v0.7/v0.8 のコア機能だったが、LoRA 路線優先のため将来検討に降格
- 詳細は ROADMAP.md の「学習機構について」セクション参照

---

## Claude Code 作業ガイダンス

### Plan mode を積極活用

設計判断が必要なバージョン（特に v0.6 以降）は、コード書く前に Plan mode で計画を確認してから実装に入る。

特に v0.8（LoRA 訓練環境）、v0.9（訓練 + 評価ループ）は、実装前にユーザーと方針確認が必須。
LoRA まわりは選択肢（Unsloth vs axolotl、データフォーマット、評価方法）が多いので、勝手に決めず相談すること。

### 既存ドキュメントを尊重

ROADMAP.md / CHANGELOG.md は手作業で維持されている。**勝手に再構成・再フォーマットしない**。追記する時は既存のフォーマットに合わせる。

### 各バージョン完了時のルーチン

1. 動作確認（具体的な確認項目はバージョンごとに定義）
2. CHANGELOG.md にエントリ追加（既存フォーマット踏襲、「目標」「新規」「動作確認済み」「制限事項」の構造を維持）
3. ROADMAP.md のバージョン計画表の状態列を「開発中」→「完了」、次バージョンを「未着手」→「開発中」に更新
4. git commit（メッセージは feat / fix / docs / refactor の prefix を使う）

### 将来検討の扱い

ROADMAP.md の「将来検討」セクション（周辺機構ライン、モバイルブリッジ、外部連携、LightClaude、ブランド戦略）は **コア v0.x 完成後** に手をつける。今は読むだけで、実装に手を出さないこと。ユーザーから明示的に指示があった時のみ着手。

---

## 開発の連携体制

このプロジェクトは複数ツールで開発されている:

| ツール | 役割 |
|---|---|
| **Claude.ai (Web/モバイル)** | 設計議論、難所相談、ROADMAP/CHANGELOG 等ドキュメントの作成・更新 |
| **Claude Code**（あなた） | 実装担当。コード書き、動作確認、リファクタ |
| **Cline + Qwen**（過去） | v0.1 までの実装担当。今後は基本使わない |
| **Ollama** | DarkClaude 本体が利用する LLM ランタイム |

設計や仕様の根本変更が必要な時は、勝手に判断せず **「これは Claude.ai で相談してから来てください」とユーザーに促す** こと。

---

## tomo_rrow さんについて

- DarkClaude プロジェクトのオーナー兼ディレクター
- AI ツール活用前提で開発を進めている
- 速度・品質・使い心地は本人基準（「自分が納得できるもの」を優先）
- **LoRA による本物の学習機構を最終目標として強く望んでいる**（重要）
- 配布は将来検討（職場 PC や同僚 PC が候補）
