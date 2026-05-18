# DarkClaude

ローカル LLM で動く Claude Code クローン。
トークン消費ゼロで「Claude Code っぽい体験」を提供することを目指す個人プロジェクト。

## 概要

- 既存の Anthropic Claude Code は API トークンに月数万円かかる
- ローカル GPU + オープンウェイトモデルで同等の体験を作る
- v0.x で機能と安定性を積み、v1.0 で配布候補を出す

詳細は [ROADMAP.md](./ROADMAP.md) と [DECISIONS.md](./DECISIONS.md) を参照。

## アーキテクチャ (Phase A 以降)

```
User
  ↓
DarkClaude (Python REPL)
  ↓ HTTP (OpenAI 互換 API)
llama-server (llama.cpp)
  ↓
Qwen3.6-35B-A3B (22GB GGUF)
```

旧 Ollama 経路も `client: ollama` で切替可能 (LoRA 検証用)。

## 動作要件

| 項目 | 最小 | 推奨 |
|------|------|------|
| RAM | 32 GB | 32 GB+ |
| VRAM | 8 GB | 8 GB+ (RTX 4060 で動作実績あり) |
| ディスク | 25 GB (モデル本体) | + 数 GB (training/) |
| OS | Windows 11 (本番) | Windows / Linux |
| Python | 3.10+ | 3.14 で動作確認 |

## セットアップ

### 1. 依存ライブラリ

```bash
pip install -r requirements.txt
```

### 2. llama.cpp バイナリ

[公式リリース](https://github.com/ggml-org/llama.cpp/releases) から CUDA 対応版をダウンロードして `~/llamacpp/` に展開。

### 3. モデルダウンロード

```powershell
Start-BitsTransfer `
  -Source "https://huggingface.co/unsloth/Qwen3.6-35B-A3B-GGUF/resolve/main/Qwen3.6-35B-A3B-UD-Q4_K_M.gguf" `
  -Destination "$env:USERPROFILE\models\Qwen3.6-35B-A3B-UD-Q4_K_M.gguf"
```

サイズ: 22.1 GB。

### 4. 起動スクリプトのパス確認

`start_llama_server.ps1` の `$llamaDir` と `$modelPath` が環境に合っているか確認。

## 起動方法

### Step 1: llama-server を起動 (別ウィンドウ)

```powershell
.\start_llama_server.ps1
```

`HTTP server listening at http://localhost:8080` が出たら準備完了 (約 1 分)。

### Step 2: DarkClaude を起動

```powershell
python main.py
```

ASCII ロゴ + `Model: qwen3.6` 表示で起動成功。

## config.json

```json
{
  "model": "qwen3.6",
  "client": "openai",
  "base_url": "http://localhost:8080",
  "think_mode": "off",
  "logging_enabled": true
}
```

| フィールド | 説明 |
|----------|------|
| `model` | モデル名 (OpenAI クライアントでは任意のラベル) |
| `client` | `"openai"` (llama-server) または `"ollama"` (Ollama daemon) |
| `base_url` | API エンドポイント (OpenAI クライアントの場合) |
| `think_mode` | `"show"` / `"hide"` / `"off"` |
| `logging_enabled` | 会話ログを `data/conversations/` に記録するか |

## llama-server 必須フラグ

`start_llama_server.ps1` に集約されていますが、手動起動時は以下が**全て必要**:

| フラグ | 役割 | 落とすと... |
|--------|------|----|
| `--jinja` | tool calling 用 chat template | tool calling 不動 |
| `--reasoning off` | thinking 抑制 | 5 分以上暴走 |
| `--reasoning-budget 0` | thinking トークン上限 0 | 同上 |
| `--n-cpu-moe 32` | MoE エキスパートを CPU オフロード | VRAM 8GB では起動失敗 |
| `-c 32768 -ctk q8_0 -ctv q8_0` | 32K コンテキスト + KV cache 量子化 | コンテキスト不足 |

## 内蔵コマンド

- `/exit`, `/quit`, `/bye` — 終了
- `/models` — 利用可能モデル一覧
- `/model <name>` — モデル切替 (一時的)
- `/setmodel <name>` — モデル切替 + config.json 永続化
- `/plan` — Plan モード切替 (write_file/bash 無効化)
- `/think show|hide|off` — Think モード切替
- `/logging` — ログ記録 ON/OFF

## トラブルシューティング

### 応答が 5 分以上返ってこない

`--reasoning off --reasoning-budget 0` フラグが llama-server 起動コマンドに含まれているか確認。
env var `LLAMA_CHAT_TEMPLATE_KWARGS` は deprecated で効果なし、フラグ経由のみ信頼可。

### config.json 編集後にデフォルトに戻る

PowerShell の `Set-Content -Encoding utf8` (5.1) は BOM を付与する。
Python の `json.loads` が BOM でパース失敗 → デフォルト config に戻る。
対策: Python から書き込むか、`-Encoding utf8NoBOM` (PS 7+) を使う。
`load_config()` は v0.11 で `utf-8-sig` 対応済みなので新規環境では問題なし。

### tool calling が発火しない

- `--jinja` フラグが付いているか
- モデルが tool calling 対応か (Qwen3.6 はネイティブ対応)
- tool 定義 SCHEMA が OpenAI 形式か

## プロジェクト構造

```
nanoclaude/
├── main.py                    # REPL + メインループ
├── clients/                   # LLM クライアント抽象化 (v0.11)
│   ├── __init__.py            # ファクトリ get_client()
│   ├── ollama_client.py       # Ollama 経由
│   └── openai_client.py       # llama-server 経由
├── tools/                     # ツール実装
│   ├── registry.py            # TOOL_SCHEMAS + dispatch
│   ├── read_file.py
│   ├── write_file.py
│   ├── bash.py
│   ├── grep.py
│   ├── glob.py
│   ├── str_replace.py
│   └── approval.py
├── session_log.py             # 会話ログ記録
├── config.json                # ランタイム設定
├── start_llama_server.ps1     # llama-server 起動スクリプト
├── requirements.txt
├── data/conversations/        # セッションログ (.gitignore 済)
├── training/                  # LoRA 学習関連 (保留中)
├── DECISIONS.md               # 設計判断記録 (ADR 風)
└── ROADMAP.md                 # バージョン計画
```

## 関連リポジトリ

- [shareAI-lab/learn-claude-code](https://github.com/shareAI-lab/learn-claude-code) — NanoClaude 教材 (本プロジェクトの起点)
- [codetwentyfive/claw-code-local](https://github.com/codetwentyfive/claw-code-local) — 参考 (Rust + Ollama)

## ライセンス

(未定義 — 個人プロジェクトのため当面非公開)

## 名前の由来

**DarkClaude** = ローカルで隠れて動く、ちょっと隠秘性のある Claude クローン。
将来配布時には Crown 系へのリブランド可能性あり (詳細 ROADMAP.md)。
