---
name: darkclaude-conventions
description: DarkClaude プロジェクト規約
keywords: [darkclaude, nanoclaude, config, tools, api, convention, 規約]
---
## 構造

api/main.py: FastAPI (port 8765)
tools/: ツール実装
clients/: LLM クライアント
prompts.py: システムプロンプト
config.json: 設定
darkclaude-app/: Tauri フロント

## ルール
- bash は PowerShell 形式
- && 不可、; を使う
- UTF-8 指定必須
