# DarkClaude PROJECT COMPASS
> 最終更新: 2026-05-23
> このファイルは「方向がぶれないための羅針盤」です。迷ったら必ずここに戻る。

---

## 1. ゴール（変えない）

**Claude Code の 60-70% レベルで個人実用できるものを作る**

| 要件 | 内容 |
|---|---|
| 無料 | ローカル優先。無料 API は最終手段 |
| 汎用 | 専門特化ではなく、Claude Code と同等の用途に使える |
| 精度優先 | まず正確に動く。速度はその後 |
| 8GB VRAM | RTX 4060 制約、LoRA 訓練できるのは 7-8B 規模まで |

---

## 2. 経緯（なぜ今ここにいるか）

```
v0.1 NanoClaude (2026-05 初旬)
  └─ Ollama + Python で最小 REPL 作成

v0.9-beta (2026-05-19)
  └─ TUI 全面完成（prompt_toolkit ベース）

Phase B-new 完成 (2026-05-22, commit 8ccbfa3)
  └─ Tauri + React + FastAPI に移行
     理由: TUI のドラッグ選択不可・PC 再現性・Claude Code 風 UI の限界

実用テスト → 精度不足と判断 (2026-05-23)
  └─ Qwen3.6 が Claude との会話で決まった計画を正確に実行できない
     → 4 改善を実装（未テスト）
     → 方針: 速度より精度

今ここ: 4 改善を Gemini OFF 状態でテストしてから次を決める
```

---

## 3. 試したこと・結果

### 実験 E1-E16（ハーネス改善）

| 実験 | 内容 | 結果 |
|---|---|---|
| E1 | CLAUDE.md 自動読込 | 3.0x 速（T01 品質低下リスク） |
| E2 | Tool scoping | 1.28x 速、副作用ゼロ |
| E3 | Tool 遅延ロード | 効果なし |
| E4 | Self-verification | 品質微低下、採用見送り |
| E5 | Skills system | 効果なし（汎用タスクではヒットせず） |
| E6 | Reflexion（失敗学習） | 1.11x 速、副作用ゼロ |
| E7 | Auto-Compaction | 1.54x 速、副作用ゼロ |
| E8 | Critic agent | E7 と同等 |
| E9 | Planner agent | 品質悪化・採用見送り |
| E10 | Ralph Loop | 小幅改善（長タスクで本領） |
| E11 | Sub-agent parallel | 効果なし（Qwen が選ばない） |
| E16c | 専用ハーネス | 1.27x 速、品質完璧 |

### 推論最適化

| 実験 | 内容 | 結果 |
|---|---|---|
| Phase 2 | Q3_K_XL 量子化 | 2.02x 速 |
| Phase 2b | context 16K 縮小 | 3.17x 速（現在のベスト） |
| Phase 3 / MTP | MTP 4方向試行 | 全失敗（MoE との相性問題） |
| Phase 1a | フラグ追加 | 効果なし |

**現在の最終構成：Q3_K_XL + context 16K + n-cpu-moe 40 = 145s**

### 精度改善（未テスト）

| 実装 | 内容 |
|---|---|
| Karpathy 4 ルール | `.darkclaude/skills/karpathy-rules.md` |
| ツール説明明確化 | glob/grep/bash の誤用防止 |
| エラー連続ヒント注入 | 2 回連続エラーで別アプローチ促す |
| Gemini Flash フォールバック | 未テスト状態（OFF にしてからテスト） |

---

## 4. 次ステップパイプライン（順番通りに）

```
Step 1: Gemini フォールバックを config で OFF
  → テスト（4 改善の効果を純粋に測定）
  → 失敗パターンを記録（→ これが次の判断材料）

Step 2: テスト結果で分岐
  ├ 満足できる精度 → 運用開始
  ├ 改善の余地あり → ハーネス強化（ツール Hook、CLAUDE.md 整理）
  └ 精度が足りない → Step 3 へ

Step 3: DeepSeek-Coder V2 Lite テスト
  → 同じタスクで Qwen3.6 と比較
  → 精度・速度どちらが良いか確認

Step 4: モデル乗換 or LoRA 判断
  → DeepSeek が良ければそのまま採用
  → LoRA で「Claude との会話パターン」に特化訓練も検討

Step 5: 速度改善（精度確保後）
  → E18: UD-Q4_K_XL 量子化（モデル DL 必要、+27%）
  → E17 再挑戦: MTP / SWIFT（条件が整えば）
  → E19-E20: フラグ・サンプリング調整

Step 6: クロードラボ設計（Opus で相談、未実施）
  → 就労継続支援 B 型施設への導入
  → RTX3050 向けモデル選定
  → Phase C（Codex 風 UI）→ D（ガードレール + Hooks）→ E（Tauri ビルド）
```

---

## 5. クロードラボ（別プロジェクト）

### 導入先
就労継続支援 B 型施設

### 設置環境
| PC | GPU | VRAM | メモリ | CPU |
|---|---|---|---|---|
| PC1 | RTX 3050 | 8GB | 16GB | Ryzen 5 5600 |
| PC2 | RTX 3050 | 8GB | 16GB | Ryzen 5 7500F |
| PC3 | RTX 4060 | 8GB | 16GB | Ryzen 5 4500 |

### 重要制約
- **各 PC が独立して動作必須**（利用者が別作業をしているため共有サーバー不可）
- RTX3050 環境向けに私用版より軽いモデルが必要

### 予定機能
- Phase C: Codex 風 UI（利用者が触りやすいシンプル版）
- Phase D: ガードレール + Hooks（業務外アクセス制限等）
- Phase E: Tauri ビルド（配布可能な .exe）

---

## 6. 保留アイデア（消さない・将来に持ち越す）

| アイデア | 概要 | 保留理由 |
|---|---|---|
| モバイルブリッジ | Tailscale + Flask でスマホから操作 | コア完成後に着手 |
| MCP クライアント | Pattern Y（20-40h）でエコシステム活用 | CodeGraph Pattern X で当面は十分 |
| SWIFT 推論最適化 | MoE との相性良く MTP より安全 | 環境整備が必要 |
| マルチエージェント討論 | Qwen + Gemini + Groq で協議 | 精度向上後に評価 |
| LoRA 専用モデル | 7B に絞って訓練で「専用 DarkClaude AI」| データ蓄積後 |
| Few-shot examples | システムプロンプトへの対話例注入 | B-1 改善の一部 |

---

## 7. 現在のファイル構成

```
C:\Users\tomo_rrow\Documents\nanoclaude\
  api/main.py              FastAPI バックエンド（port 8765）
  tools/                   ツール群（bash/read_file/write_file/str_replace/glob）
  tools/codegraph_explore.py  CodeGraph 統合（Phase A.5 完了）
  clients/                 LLM クライアント
  prompts.py               システムプロンプト
  config.json              設定（use_gemini_fallback を OFF にしてテスト）
  .darkclaude/
    skills/karpathy-rules.md   Karpathy 4 ルール（実装済み）
    reflexion.md               過去の失敗教訓（E6）
  darkclaude-app/          Tauri + React フロントエンド
  start_llama_server.ps1   llama-server 起動スクリプト
  benchmarks/              T01-T05, T07-T13（T06 は無効化）

ブランチ: experiments/phase-b-textual
```

---

## 8. llama-server 必須フラグ

```powershell
--jinja                    # tool calling 必須
--reasoning off            # Qwen3.6 thinking 暴走防止
--reasoning-budget 0       # 同上
--n-cpu-moe 40             # MoE を CPU オフロード（8GB VRAM 制約）
-c 16384                   # context 16K（Phase 2b で縮小）
-ctk q8_0 -ctv q8_0       # KV cache 量子化
```

**注意**: `--no-mmap --mlock` は RTX 4060 + 32GB RAM 環境でフリーズの原因、使わない

---

## 9. モデル切り替え指針

| タスク | 使うモデル |
|---|---|
| 戦略・設計・重要判断 | Claude Opus（このチャット） |
| 調査・実装・準備 | Claude Sonnet（このチャット） |
| 単純な一問一答・整形 | Haiku 推奨 |
| コーディング実装タスク | Claude Code + qwen-coder-cc |
| ローカル本番実装 | DarkClaude + Qwen3.6（精度テスト通過後） |

---

*このファイルを `C:\Users\tomo_rrow\Documents\nanoclaude\docs\PROJECT-COMPASS.md` に配置してください*
