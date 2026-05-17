"""
eval.py - 訓練前後の応答比較評価

Usage:
    python eval.py --adapter output/<run_id>/adapter [--out eval_results]
    python eval.py --out eval_results  # ベースモデルのみ（adapter なし）
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# Windows 環境での SSL 証明書問題対応:
# hf_transfer は Rust 製で Python の truststore を bypass する。
# 無効化して Python requests に戻し、truststore で OS 証明書ストアを使う。
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


def load_prompts(prompts_path: Path) -> list[dict]:
    prompts = []
    with prompts_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    prompts.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return prompts


def generate_response(model, tokenizer, prompt: str, max_new_tokens: int = 512) -> str:
    """1 つのプロンプトに対して応答を生成する。"""
    from unsloth import FastLanguageModel

    FastLanguageModel.for_inference(model)

    messages = [{"role": "user", "content": prompt}]
    try:
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
    except Exception:
        text = f"USER: {prompt}\nASSISTANT:"

    inputs = tokenizer(text, return_tensors="pt").to("cuda")
    outputs = model.generate(
        **inputs,
        max_new_tokens=max_new_tokens,
        temperature=0.7,
        do_sample=True,
        pad_token_id=tokenizer.eos_token_id,
    )
    generated = outputs[0][inputs["input_ids"].shape[1]:]
    return tokenizer.decode(generated, skip_special_tokens=True).strip()


def load_base_model(model_name: str, max_seq_length: int):
    from unsloth import FastLanguageModel

    print(f"[eval] ベースモデルロード: {model_name}")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=model_name,
        max_seq_length=max_seq_length,
        load_in_4bit=True,
        dtype=None,
    )
    return model, tokenizer


def load_adapter(model, tokenizer, adapter_path: Path):
    from peft import PeftModel

    print(f"[eval] LoRA adapter ロード: {adapter_path}")
    model = PeftModel.from_pretrained(model, str(adapter_path))
    return model, tokenizer


def eval_run(args: argparse.Namespace) -> None:
    script_dir = Path(__file__).parent.resolve()

    # eval プロンプト読み込み
    prompts_path = script_dir / "eval_set" / "prompts.jsonl"
    prompts = load_prompts(prompts_path)
    if not prompts:
        print("[eval] ERROR: eval_set/prompts.jsonl が空です。")
        sys.exit(1)
    print(f"[eval] プロンプト数: {len(prompts)}")

    # meta.json から model 名と adapter パスを取得
    adapter_path: Path | None = None
    model_name = "unsloth/Qwen3-8B"
    max_seq_length = 2048
    run_id = "base_only"

    if args.adapter:
        adapter_path = Path(args.adapter)
        if not adapter_path.is_absolute():
            adapter_path = script_dir / adapter_path
        meta_path = adapter_path.parent / "meta.json"
        if meta_path.exists():
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            model_name = meta.get("model", model_name)
            run_id = meta.get("run_id", run_id)

    out_dir = script_dir / args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    # ベースモデル応答生成
    model, tokenizer = load_base_model(model_name, max_seq_length)
    base_responses: list[str] = []
    for p in prompts:
        resp = generate_response(model, tokenizer, p["prompt"])
        base_responses.append(resp)
        print(f"  [base] {p['id']}: {resp[:60]}...")

    # adapter あり応答生成
    tuned_responses: list[str | None] = [None] * len(prompts)
    if adapter_path and adapter_path.exists():
        model, tokenizer = load_adapter(model, tokenizer, adapter_path)
        for i, p in enumerate(prompts):
            resp = generate_response(model, tokenizer, p["prompt"])
            tuned_responses[i] = resp
            print(f"  [tuned] {p['id']}: {resp[:60]}...")
    else:
        print("[eval] adapter なし — ベースモデル結果のみ出力します。")

    # Markdown 出力
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_path = out_dir / f"{timestamp}_{run_id}.md"

    with out_path.open("w", encoding="utf-8") as f:
        f.write(f"# DarkClaude eval — {run_id}\n\n")
        f.write(f"- 実行日時: {timestamp}\n")
        f.write(f"- モデル: {model_name}\n")
        f.write(f"- adapter: {adapter_path or 'なし'}\n")
        f.write(f"- プロンプト数: {len(prompts)}\n\n")
        f.write("---\n\n")

        for i, p in enumerate(prompts):
            f.write(f"## [{p['id']}] {p['category']} — `{p['prompt']}`\n\n")
            f.write("### ベースモデル応答\n\n")
            f.write(f"```\n{base_responses[i]}\n```\n\n")

            if tuned_responses[i] is not None:
                f.write("### 訓練後応答\n\n")
                f.write(f"```\n{tuned_responses[i]}\n```\n\n")
            else:
                f.write("### 訓練後応答\n\n")
                f.write("（adapter なし — 省略）\n\n")

            f.write("### 手動採点\n\n")
            f.write("- 品質: [ ] better / [ ] worse / [ ] same\n")
            f.write("- メモ: \n\n")
            f.write("---\n\n")

    print(f"[eval] Markdown 出力: {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="訓練前後の応答比較評価")
    parser.add_argument("--adapter", default=None,
                        help="LoRA adapter ディレクトリ（省略時はベースモデルのみ）")
    parser.add_argument("--out", default="eval_results",
                        help="出力ディレクトリ (default: eval_results)")
    args = parser.parse_args()
    eval_run(args)


if __name__ == "__main__":
    main()
