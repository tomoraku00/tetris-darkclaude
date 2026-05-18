# DarkClaude 意思決定記録

軽量版 ADR (Architecture Decision Record)。設計判断の経緯と理由を残す。
時系列降順（新しい判断ほど上）。

---

## 2026-05-18: 「完成」を v0.9 + v0.10 の完了時点と定義

### 経緯

1. v0.9 を A+C 並走 (LoRA 保留) に再定義
   （同日付の別判断、本ファイルの下方参照）
2. その後の議論で v0.9 完了後の方向性を整理:
   - 配布検討 (元 v1.0、Phase 2) は急ぎではない
   - 「自分用に納得できる状態」を当面の到達目標とする
   - UI 周りの作り込みも必要だが A+C とは性質が違うので分離する

### 判断

- v0.9 (A+C 並走): エージェント能力の作り込み
- v0.10 (UI 整備): 使い心地の調整
- 上記 2 つの完了時点をもって「DarkClaude 完成」とする
- v1.0 以降 (配布、LoRA 再開等) は需要・条件発生時に都度判断

### バージョン番号についての補足

v0.10 を採用した理由 (v1.0 や無番号ではなく):
- A+C と UI 整備は性質が違うため分離した方が完了基準が明確
- v1.0 は配布版に温存する (将来配布を出す際の混乱回避)
- v0.9 に内包すると v0.9 スコープが膨らみすぎる

### 再判断トリガ

- 配布需要が発生した時点で v1.0 計画を起動
- LoRA 再開条件が満たされた時点で別 minor 番号で再開

---

## 2026-05-18: v0.9 から LoRA 訓練を保留

### 経緯

1. v0.8 で Qwen3-8B が RTX 4060 8GB では訓練不可と判明
   （CLAUDE.md 観察記録「v0.8 で判明: Qwen3-8B 4bit QLoRA は ...」参照）
2. 整合性確保のため代案 3 つを検討:
   - X 案: 本体も Qwen3-4B 化
   - Y 案: 訓練 4B / 本体 8B、LoRA は研究目的に留める
   - Z 案: 8B 訓練環境を別途確保（Z-a クラウド / Z-b GPU 増強）
3. X 案を採用候補として Qwen3-4B 性能テストを実施
   （CLAUDE.md 観察記録「v0.8 完了後判断: Qwen3-4B は ...」参照）→ 不採用
4. Y 案は LoRA が本体に効かない（adapter のベースモデル不一致）ため
   DarkClaude のコア価値が崩れる → 不採用
5. Z-a / Z-b は追加費用発生、現状予算なし → 見送り

### 判断

- LoRA 訓練は保留（killed ではなく paused）
- 本体 Ollama は qwen3:8b 維持
- v0.8 で構築した training/ 環境とコードはそのまま残し、再開時の起点とする
- configs/lora_default.yaml の Qwen3-4B 設定も保持

### 再開トリガ

- ハードウェア追加（VRAM 16GB+ GPU、例: RTX 5060 Ti 16GB）
- 予算割当変更
- Qwen3-4B 相当のモデルがエージェント用途で十分強くなった将来時点での再評価

### v0.9 方針変更

LoRA 訓練ループから「プロンプト・ツール作り込み」（A+C 並走）に再定義。
詳細は ROADMAP.md v0.9 セクション参照。


## 2026-05-18: バックエンドを Ollama から llama.cpp + Qwen3.6 に切り替え (Phase A)

### 経緯

1. Phase B/B' で 3 モデル (qwen3:8b, qwen3.5:9b, qwen2.5-coder:7b) を DarkClaude のスモークテストにかけて全滅
   - qwen3:8b: 英語+装飾、analyze-first 病、Test 3 誤解釈
   - qwen3.5:9b: 日本語だが大量幻覚、chat template 境界トークン暴露 (4 分応答)
   - qwen2.5-coder:7b: tool calling 一度も発火せず
2. ベースモデル交換だけでは解決しないと判断、Phase A (llama.cpp + Qwen3.6-35B-A3B 大改修) に踏み切る
3. Phase A1 (インフラ単体): llama.cpp Windows CUDA 12.4 b9209 + Qwen3.6-35B-A3B-UD-Q4_K_M (22.1 GB) で起動成功、10.52 t/s 確認
4. Phase A2 (tool calling 単体): OpenAI 互換 API で完璧動作 (293 tokens プロンプト処理 + tool_calls 返却で 10 秒)
5. Phase A3 (影響範囲特定): tools/*.py の SCHEMA が既に OpenAI 互換 → スキーマ変換不要、改修範囲が大幅縮小
6. Phase A4 (リファクタ): clients/ 抽象化レイヤー新規 3 ファイル + main.py 5 箇所修正
7. Phase A5 (スモークテスト): 3/3 PASS

### 判断

- **バックエンド**: llama.cpp (llama-server) に変更。Ollama 経路は OllamaClient として残存 (LoRA 検証等用)
- **モデル**: Qwen3.6-35B-A3B-UD-Q4_K_M.gguf (Unsloth Quant)
- **アーキテクチャ**: LLMClient 抽象 (config.json の "client" フィールドで切替)
- **デフォルト**: client="openai" + base_url="http://localhost:8080"

### 必須の起動フラグ (落とすと致命的)

llama-server に以下**全て**必須:
- `--jinja`: tool calling 用 chat template
- `--reasoning off`: thinking 完全停止 (Qwen3.6 必須、env var LLAMA_CHAT_TEMPLATE_KWARGS は効かない)
- `--reasoning-budget 0`: thinking トークン上限を 0 に強制
- `--n-cpu-moe 32`: 8GB VRAM 制約下で MoE エキスパートを CPU オフロード
- `-c 32768 -ctk q8_0 -ctv q8_0`: 32K コンテキスト + KV cache 量子化

これらが揃わないと:
- `--jinja` なし → tool calling 不動
- `--reasoning off/budget 0` なし → 内部 thinking で 5 分+ 暴走 (実測 6 分超で中断)
- `--n-cpu-moe` なし → VRAM 不足で起動失敗

起動コマンド本体は `start_llama_server.ps1` を参照。

### Phase A の数値結果

| テスト | qwen3:8b (旧) | Qwen3.6 (新) |
|--------|--------------|-------------|
| 簡単な挨拶 | 1m 52s | 約 50s |
| main.py 読み込み | 失敗 (英語マークダウン) | 106s、日本語、簡潔 |
| str_replace 即発火 | 失敗 (ツール未発火) | 175s、即発火 |
| 空出力扱い | 失敗 (誤解釈) | 94s、正確な解釈 |

応答速度のボトルネックはプロンプト処理 (SYSTEM プロンプト + tools schema で 2300 tokens / 25-50 t/s)。生成は 10-12 t/s。

### LoRA 路線の扱い

Phase A 成功により、LoRA 復活の必要性は**再評価対象**:
- 表層の問題 (英語、装飾、analyze-first、空出力誤解釈) は解決済み
- Phase A6 (安定化) で残る癖が見えるまで LoRA は不要
- 残るとすれば: 装飾の頑固さ、長時間会話での品質低下、特定指示への抵抗

### 影響を受ける既存決定

- **2026-05-18 「v0.9+v0.10 で完成」**: Phase A 完了で**再定義**。Phase A 完了が新しい "feature complete" の実質的基準
- **2026-05-18 「LoRA 保留」**: 維持 (Phase A6 後に再判断)

### 副次的な技術メモ

- PowerShell `Set-Content -Encoding utf8` は (Windows PowerShell 5.1 では) UTF-8 BOM を付与し、Python の `json.loads(text, encoding="utf-8")` がパース失敗する。対策: `load_config()` を `encoding="utf-8-sig"` に修正済み。
- Qwen3.6 の chat template は Jinja で、`enable_thinking=false` の env var 経由は deprecated かつ tool 経路で効かない。フラグ経由 (`--reasoning off`) のみ信頼可。
- main.py の `save_config({"model": ..., "think_mode": ..., "logging_enabled": ...})` が 3 キーだけ書く設計で、config.json の追加フィールド (client, base_url) を上書きしてしまうバグを Phase A 検証中に発見。将来的に修正候補だが今回は config.json 直書きで回避。
