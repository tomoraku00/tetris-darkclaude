# DarkClaude training/

DarkClaude LoRA 訓練パイプライン。本体 (Python 3.14) とは完全に隔離した
Python 3.12 専用 venv で動作する。

---

## 前提環境

| 項目 | 値 |
|---|---|
| OS | Windows 11 |
| GPU | RTX 4060 / VRAM 8GB |
| Python | 3.12.x（本体 3.14 とは別） |
| PyTorch | **2.11.0+cu126 必須**（2.10 では xformers cpp 拡張が読み込まれずクラッシュ） |
| CUDA | 12.6 対応 torch wheel（ドライバは 12.x 以上であれば OK） |

---

## セットアップ手順

### 1. Python 3.12 の確認

```powershell
py -3.12 --version
```

見つからない場合:

```powershell
py install 3.12
```

### 2. venv 作成

```powershell
cd training
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. PyTorch（CUDA 12.6）インストール

**torch は requirements.txt より先に手動でインストールする。**
Windows では index URL の指定が必要なため別立て。

**torch 2.11.0+cu126 を指定すること（2.10.x では xformers が cpp 拡張を読み込めずクラッシュする）。**

```powershell
pip install "torch==2.11.0+cu126" torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126
```

> CUDA ドライバが 12.6 未満の場合は `cu124` に変更してください。

### 4. 残りの依存パッケージ

```powershell
pip install -r requirements.txt
```

### 5. CUDA 動作確認

```powershell
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

期待出力例:
```
True  NVIDIA GeForce RTX 4060
```

### 6. Unsloth 動作確認

**`import datasets` を先に実行しないとクラッシュする（Windows 既知問題）。**

```powershell
python -c "import datasets; from unsloth import FastLanguageModel; print('unsloth OK')"
```

---

## パイプライン実行

### prepare.py — 会話ログ → ChatML 変換

```powershell
python prepare.py
# または
python prepare.py --input ../data/conversations --output prepared
```

v0.7 で蓄積された `data/conversations/*.jsonl` を読み込み、
`prepared/YYYYMMDD-HHMMSS.jsonl` に ChatML 形式で出力する。
ファイルがない場合も正常終了（ログ収集が進めば自動的に増える）。

### train.py — LoRA 訓練

**サニティチェック（公開データ 100 step）:**

```powershell
python train.py --config configs/lora_default.yaml ^
    --hf-dataset tatsu-lab/alpaca --hf-max-samples 1000 ^
    --max-steps 100
```

> HF データセット選定理由: tatsu-lab/alpaca は 52K の汎用 instruction-following
> データセット。CC BY-NC 4.0、ローカル研究用途に問題なし。
> 1000 件サブセットで 100 step のパイプライン動作確認に十分な規模。

**本番訓練（実会話ログが溜まってから）:**

```powershell
python train.py --config configs/lora_default.yaml --data prepared/<file>.jsonl
```

出力: `output/<run_id>/adapter/` に LoRA adapter が保存される。

### eval.py — 訓練前後の比較

```powershell
python eval.py --adapter output/<run_id>/adapter
```

`eval_results/<timestamp>_<run_id>.md` に比較 Markdown が出力される。
手動採点欄 (`[ ] better / [ ] worse / [ ] same`) は自分で記入する。

### deploy.py — Ollama デプロイ（v0.9 で実装）

```powershell
python -c "import training.deploy"   # import のみ確認（v0.8 はスケルトン）
```

---

## ディレクトリ構成

```
training/
├── .venv/              # Python 3.12 専用 venv（git 除外）
├── README.md           # このファイル
├── requirements.txt    # 訓練側 deps
├── prepare.py          # JSONL → ChatML 変換
├── train.py            # Unsloth 訓練
├── eval.py             # 訓練前後の比較
├── deploy.py           # スケルトン（v0.9 で実装）
├── configs/
│   └── lora_default.yaml
├── eval_set/
│   └── prompts.jsonl   # 評価プロンプト（本番 20 件はユーザーが手書き）
├── prepared/           # prepare.py の出力（git 除外）
├── output/             # LoRA adapter 出力（git 除外）
└── eval_results/       # 評価 Markdown 出力（git 除外）
```

---

## VRAM に関する注意

- **Qwen3-4B 4bit QLoRA**: ピーク ~3.5GB（RTX 4060 / 8GB で余裕あり、サニティチェック推奨）
- **Qwen3-8B 4bit QLoRA**: ベースモデルだけで ~7GB を消費。RTX 4060 8GB では訓練オーバーヘッドがほぼ収まらず 1 step が 50〜130 秒に達する
  - Unsloth の fused CE loss が first forward pass 後の free VRAM ≈ 0 を検出して `RuntimeError` を投げる（対処: CHANGELOG.md v0.8 参照）
  - サニティチェックには `unsloth/Qwen3-4B` を使うこと
- `configs/lora_default.yaml` の `model.name` を変更することでモデルを切り替え可能
- 訓練中は Ollama を停止しておくと VRAM が確保しやすい:
  `ollama stop` または タスクトレイから終了

---

## トラブルシューティング

| 症状 | 対処 |
|---|---|
| `torch.cuda.is_available() == False` | CUDA ドライバ更新、または cu126 → cu124 に変更して再インストール |
| `ImportError: cannot import name 'FastLanguageModel'` | `pip install unsloth` が失敗している。`pip install --upgrade unsloth` を試す |
| プロセスが exit -1073741819 (0xC0000005) でクラッシュ | **Windows 既知問題**: Unsloth 2026.5.2 + torch 2.11 の import order バグ。`train.py` / `eval.py` 先頭の `import datasets` が必須。詳細は CHANGELOG.md v0.8 参照 |
| OOM (Out of Memory) | `max_seq_length` を半分に、`gradient_accumulation_steps` を増やす |
| `dataloader` エラー | Windows 環境のため `dataloader_num_workers=0` が train.py にセット済み、変更不要 |
| xformers が "Skipping import of cpp extensions" と表示 | torch 2.10.x を使っている。`pip install "torch==2.11.0+cu126" --index-url ...` でアップグレード |
