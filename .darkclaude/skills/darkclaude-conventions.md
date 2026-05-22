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


## 外部プロジェクトのファイルを読む場合

nanoclaude 以外のプロジェクトのファイルは絶対パスで read_file を使うこと。

例:
- read_file(C:/dev/src/lib/gaugeAnalyzer.ts)
- read_file(C:/dev/services/yolo-cloud-run/main.py)

bash の Get-Content は使わない。必ず read_file を使うこと。
glob も nanoclaude 内しか検索できないので外部プロジェクトには使わない。
