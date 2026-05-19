# DarkClaude ベンチマーク基盤

各実験 (E1-E15) の効果を定量的に測定するためのベンチマークタスク集と評価フレームワーク。

## 前提条件

- **LLM サーバーが起動していること** (Ollama または llama-server)
- Python 3.11+
- pytest: `pip install pytest`

## タスク一覧 (T01-T05)

| ID | カテゴリ | タスク内容 | 評価方法 |
|----|---------|-----------|---------|
| T01 | 読み取り | ファイル構造要約 | キーワード 5/5 検出 |
| T02 | 単一修正 | Syntax error 修正 | `py_compile` 通過 |
| T03 | リファクタ | `parse_date` 関数整理 | pytest 5/5 通過 |
| T04 | 多ファイル | 関数リネーム (3 ファイル) | grep + pytest |
| T05 | TDD | `add` 関数実装 | pytest 通過数/5 |

## 実行方法

```bash
# Ollama 使用時
python benchmarks/runner.py \
  --version v0.9-beta \
  --output benchmarks/reports/v0.9-beta.json \
  --client ollama \
  --model qwen3:8b

# llama-server 使用時
python benchmarks/runner.py \
  --version v0.9-beta \
  --output benchmarks/reports/v0.9-beta.json \
  --client openai \
  --base-url http://localhost:8080

# T01 のみ
python benchmarks/runner.py \
  --tasks T01_summarize_structure \
  --version test \
  --output benchmarks/reports/t01.json \
  --client ollama
```

## 比較

```bash
python benchmarks/compare.py \
  benchmarks/reports/v0.9-beta.json \
  benchmarks/reports/exp-feature-x.json
```

## ディレクトリ構造

```
benchmarks/
├── runner.py          # ベンチマーク実行
├── compare.py         # バージョン間比較
├── fixtures/          # テスト素材
│   ├── small_project/ # T01 用
│   ├── bug_files/     # T02 用
│   ├── refactor/      # T03 用
│   ├── multi_file/    # T04 用
│   └── test_loop/     # T05 用
├── tasks/             # タスク定義
│   ├── T01_summarize_structure/
│   ├── T02_fix_syntax_error/
│   ├── T03_refactor_function/
│   ├── T04_multi_file_change/
│   └── T05_test_fix_loop/
└── reports/           # 実行結果 (v0.9-beta.json のみ git 管理)
```

## ベースライン記録手順

1. サーバーを起動する
2. `runner.py` を全タスクで実行
3. `reports/v0.9-beta.json` が生成されたら `git add -f` してコミット

```bash
git add -f benchmarks/reports/v0.9-beta.json
git commit -m "chore(bench): v0.9-beta ベースラインスコアを記録"
```
