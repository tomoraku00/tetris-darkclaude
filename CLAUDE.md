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

### 完了
- **v0.1**: Ollama 会話 REPL、ASCII アートロゴ、`/exit` 等コマンド

### 開発中
- **v0.2** (read_file / write_file ツール): **要復旧**
  - 状況: 以前 Cline + qwen2.5-coder:7b で実装途中、`tools` フォルダがフォルダではなく 0 バイトの空ファイルになってしまった状態
  - 必要作業:
    1. 空ファイル `tools` を削除（`Remove-Item tools` または `rm tools`）
    2. `tools/` ディレクトリを作成
    3. 配下に `__init__.py`, `registry.py`, `read_file.py`, `write_file.py` を作成
    4. `main.py` に tool 呼び出しループを統合
  - 実装着手前に `dir`, `type main.py`, `git status` で現状を確認すること

### 次以降の予定

ROADMAP.md のバージョン計画表参照。流れとしては:

```
v0.3 (bash) → v0.4 (grep/glob) → v0.5 (Plan モード) → v0.6 (権限承認)
  → v0.7 (軽量会話ログ収集、LoRA データの土台)
  → v0.8 (LoRA 訓練環境構築)
  → v0.9 (初回 LoRA 訓練 + 評価ループ)
  → v1.0 (LoRA 込み配布)
```

v0.7 以降は LoRA パイプラインに向けた整備期。詳細は ROADMAP.md の「学習機構について」セクション参照。

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

## ディレクトリ構造（目標）

```
darkclaude/
├── CLAUDE.md           # このファイル
├── ROADMAP.md          # バージョン計画と将来検討
├── CHANGELOG.md        # 完了バージョン履歴
├── README.md
├── main.py             # REPL エントリポイント
├── requirements.txt
├── .gitignore
├── tools/              # ★ v0.2 で本格化
│   ├── __init__.py
│   ├── registry.py     # TOOL_SCHEMAS と dispatch
│   ├── read_file.py    # v0.2
│   ├── write_file.py   # v0.2
│   ├── bash.py         # v0.3 (未着手)
│   ├── grep.py         # v0.4 (未着手)
│   └── glob.py         # v0.4 (未着手)
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
