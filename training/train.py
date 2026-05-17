"""
train.py - Unsloth + 4bit QLoRA 訓練スクリプト

Usage:
    # 準備済みローカル JSONL で訓練
    python train.py --config configs/lora_default.yaml --data prepared/<file>.jsonl [--max-steps N]

    # HuggingFace データセットで訓練（サニティチェック用）
    python train.py --config configs/lora_default.yaml --hf-dataset tatsu-lab/alpaca --hf-max-samples 1000 --max-steps 100
"""
import argparse
import json
import os
import secrets
import sys
from datetime import datetime
from pathlib import Path

import yaml

# Windows 環境での SSL 証明書問題対応:
# hf_transfer は Rust 製で Python の truststore を bypass する。
# 無効化して Python requests に戻し、truststore で OS 証明書ストアを使う。
# UNSLOTH_DISABLE_STATISTICS: Unsloth の HF 統計ダウンロードをスキップ
#   （これも hf_transfer で行われ SSL エラーでハングする）。
import os as _os
_os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"
_os.environ["UNSLOTH_DISABLE_STATISTICS"] = "1"
_os.environ["HF_HUB_DISABLE_XET"] = "1"      # hf-xet は独自 SSL で truststore を bypass する
try:
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass

# ※ import 順序重要、入れ替え禁止。
# Unsloth 2026.5.2 + torch 2.11 + Windows において、
# `from unsloth import ...` より前に `import datasets` を実行しないと
# unsloth_zoo 内の遅延 import で STATUS_ACCESS_VIOLATION (0xC0000005)
# を起こす（Python 例外として捕まらない）。
# 詳細: CHANGELOG.md v0.8 エントリ参照。
import datasets  # noqa: E402  isort:skip


VRAM_WARN_GB = 7.5  # これを超えたら警告


def load_config(config_path: Path) -> dict:
    with config_path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_local_dataset(data_path: Path):
    """準備済み ChatML JSONL を datasets.Dataset として返す。"""
    from datasets import Dataset

    samples = []
    with data_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                samples.append(json.loads(line))
    if not samples:
        raise ValueError(f"データが空です: {data_path}")
    return Dataset.from_list(samples)


def load_hf_dataset(dataset_name: str, max_samples: int):
    """
    HuggingFace データセットをロードし ChatML 形式に変換する。
    選定理由（tatsu-lab/alpaca）:
      - 52K の汎用 instruction-following サンプルで広く使われている標準ベンチマーク
      - ライセンス: CC BY-NC 4.0（ローカル研究用途に問題なし）
      - 専用フォーマット変換不要、instruction/input/output 構造が単純
      - 1000 件サブセットで 100 step のパイプライン動作確認に十分
    """
    from datasets import load_dataset

    print(f"[train] HF データセットロード: {dataset_name} (最大 {max_samples} 件)")
    ds = load_dataset(dataset_name, split="train")

    def to_chatml(example):
        instruction = example.get("instruction", "")
        inp = (example.get("input") or "").strip()
        output = example.get("output", "")
        user_content = f"{instruction}\n{inp}".strip() if inp else instruction
        return {
            "messages": [
                {"role": "user", "content": user_content},
                {"role": "assistant", "content": output},
            ]
        }

    ds = ds.map(to_chatml, remove_columns=ds.column_names)
    ds = ds.select(range(min(max_samples, len(ds))))
    print(f"[train] ロード完了: {len(ds)} 件")
    return ds


def format_with_chat_template(dataset, tokenizer):
    """messages[] をモデルの chat template でテキスト化する。"""

    def apply_template(examples):
        texts = []
        for msgs in examples["messages"]:
            try:
                text = tokenizer.apply_chat_template(
                    msgs,
                    tokenize=False,
                    add_generation_prompt=False,
                )
            except Exception:
                # tool_calls 等が chat template に非対応の場合はシンプル変換
                text = "\n".join(
                    f"{m['role'].upper()}: {m.get('content', '')}"
                    for m in msgs
                    if m.get("content")
                )
            texts.append(text)
        return {"text": texts}

    return dataset.map(apply_template, batched=True, remove_columns=["messages"])


def log_vram(label: str) -> float:
    """GPU VRAM 使用量を GB 単位でログ出力し、値を返す。"""
    try:
        import torch
        allocated = torch.cuda.memory_allocated() / 1024 ** 3
        reserved = torch.cuda.memory_reserved() / 1024 ** 3
        print(f"[train] VRAM {label}: allocated={allocated:.2f}GB  reserved={reserved:.2f}GB")
        if reserved > VRAM_WARN_GB:
            print(f"[train] ⚠ VRAM {reserved:.2f}GB > {VRAM_WARN_GB}GB 警告！")
        return reserved
    except Exception:
        return 0.0


def train(args: argparse.Namespace) -> None:
    import torch
    from unsloth import FastLanguageModel
    from transformers import TrainingArguments
    from trl import SFTTrainer

    config_path = Path(args.config)
    script_dir = Path(__file__).parent.resolve()
    cfg = load_config(script_dir / config_path if not config_path.is_absolute() else config_path)

    mc = cfg["model"]
    lc = cfg["lora"]
    tc = cfg["training"]

    # run_id と出力先
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S") + "_" + secrets.token_hex(3)
    output_dir = script_dir / tc.get("output_dir", "output") / run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"[train] run_id: {run_id}")
    print(f"[train] 出力: {output_dir}")

    # モデルロード
    print(f"[train] モデルロード: {mc['name']}")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=mc["name"],
        max_seq_length=mc.get("max_seq_length", 2048),
        load_in_4bit=mc.get("load_in_4bit", True),
        dtype=None,  # auto
        device_map={"": 0},  # bnb4bit は CPU dispatch を許容しないため GPU 固定
    )
    log_vram("モデルロード後")

    # LoRA アダプター設定
    model = FastLanguageModel.get_peft_model(
        model,
        r=lc["r"],
        target_modules=lc["target_modules"],
        lora_alpha=lc["lora_alpha"],
        lora_dropout=lc["lora_dropout"],
        bias=lc["bias"],
        use_gradient_checkpointing="unsloth",
        random_state=42,
    )

    # データセット準備
    if args.hf_dataset:
        dataset = load_hf_dataset(args.hf_dataset, args.hf_max_samples)
    elif args.data:
        data_path = Path(args.data)
        if not data_path.is_absolute():
            data_path = script_dir / data_path
        dataset = load_local_dataset(data_path)
    else:
        raise ValueError("--data または --hf-dataset のどちらかを指定してください。")

    dataset = format_with_chat_template(dataset, tokenizer)
    print(f"[train] 訓練サンプル数: {len(dataset)}")

    # 訓練引数
    max_steps = args.max_steps if args.max_steps is not None else -1
    use_bf16 = torch.cuda.is_bf16_supported()
    training_args = TrainingArguments(
        output_dir=str(output_dir),
        per_device_train_batch_size=tc.get("per_device_train_batch_size", 1),
        gradient_accumulation_steps=tc.get("gradient_accumulation_steps", 4),
        num_train_epochs=tc.get("num_train_epochs", 2),
        max_steps=max_steps,
        learning_rate=tc.get("learning_rate", 2e-4),
        warmup_steps=tc.get("warmup_steps", 5),
        logging_steps=tc.get("logging_steps", 1),
        save_steps=tc.get("save_steps", 50),
        optim=tc.get("optim", "adamw_8bit"),
        fp16=not use_bf16,
        bf16=use_bf16,
        seed=42,
        dataloader_num_workers=0,  # Windows で必要
        report_to="none",
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=mc.get("max_seq_length", 2048),
        dataset_num_proc=1,
        packing=False,
        args=training_args,
    )

    log_vram("訓練開始前")
    torch.cuda.empty_cache()  # fused CE loss の VRAM チェック前に未使用キャッシュを解放
    log_vram("empty_cache 後")
    print(f"[train] 訓練開始 (max_steps={'∞ (epoch ベース)' if max_steps == -1 else max_steps})")
    trainer.train()
    log_vram("訓練終了後")

    # LoRA adapter 保存
    adapter_path = output_dir / "adapter"
    model.save_pretrained(str(adapter_path))
    tokenizer.save_pretrained(str(adapter_path))
    print(f"[train] LoRA adapter 保存: {adapter_path}")

    # run メタデータ保存
    meta = {
        "run_id": run_id,
        "model": mc["name"],
        "config": str(config_path),
        "data": args.hf_dataset or str(args.data),
        "max_steps": max_steps,
        "adapter_path": str(adapter_path),
    }
    (output_dir / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[train] 完了: {output_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Unsloth 4bit QLoRA 訓練")
    parser.add_argument("--config", default="configs/lora_default.yaml",
                        help="YAML 設定ファイル")
    parser.add_argument("--data", default=None,
                        help="準備済み JSONL ファイルパス")
    parser.add_argument("--hf-dataset", default=None,
                        help="HuggingFace データセット名（例: tatsu-lab/alpaca）")
    parser.add_argument("--hf-max-samples", type=int, default=1000,
                        help="HF データセットから使用する最大サンプル数 (default: 1000)")
    parser.add_argument("--max-steps", type=int, default=None,
                        help="最大ステップ数（省略時は num_train_epochs で制御）")
    args = parser.parse_args()

    if args.data is None and args.hf_dataset is None:
        parser.error("--data または --hf-dataset のどちらかを指定してください。")

    train(args)


if __name__ == "__main__":
    main()
