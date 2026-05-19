"""DarkClaude entry point."""
import argparse
import json
import os
import sys
import time
from pathlib import Path


def _load_config() -> dict:
    config_path = Path(__file__).parent / "config.json"
    if config_path.exists():
        try:
            return json.loads(config_path.read_text(encoding="utf-8-sig"))
        except Exception:
            pass
    return {"model": "qwen3:8b"}


def run_oneshot(
    prompt: str,
    workdir: str | None,
    output_json: str | None,
    model_override: str | None,
    client_override: str | None = None,
    base_url_override: str | None = None,
) -> int:
    """非対話モード: プロンプト 1 回実行 → JSON 出力。ベンチマーク runner から呼ばれる。"""
    if workdir:
        os.chdir(workdir)

    config = _load_config()
    model = model_override or config.get("model", "qwen3:8b")
    if client_override:
        config["client"] = client_override
    if base_url_override:
        config["base_url"] = base_url_override
    think_mode = "hide"  # 思考ブロックは非表示で高速化

    from clients import get_client
    from tui.output import OutputBuffer
    from tui.chat import chat_turn

    client = get_client(config)
    output = OutputBuffer()
    state: dict = {
        "model": model,
        "think_mode": think_mode,
        "plan_mode": False,
        "thinking": "",
        "is_busy": False,
    }
    messages: list = []

    def auto_approve(name: str, args: dict) -> str:
        """ベンチマーク用: 全ツール自動承認。"""
        return "allow_once"

    start = time.monotonic()
    try:
        chat_turn(
            output=output,
            state=state,
            app=None,
            messages=messages,
            user_input=prompt,
            model=model,
            client=client,
            plan_mode=False,
            think_mode=think_mode,
            allowed_write_paths=set(),
            allowed_bash_commands=set(),
            session_log=None,
            approval_fn=auto_approve,
        )
    except Exception as e:
        print(f"[run_oneshot ERROR] {type(e).__name__}: {e}", file=sys.stderr)

    duration = time.monotonic() - start
    tool_call_count = sum(1 for m in messages if m.get("role") == "tool")
    text_output = "\n".join(output.get_plain_lines())

    result = {
        "output": text_output,
        "tool_calls": tool_call_count,
        "duration": round(duration, 2),
    }

    if output_json:
        Path(output_json).write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    else:
        print(result["output"])

    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DarkClaude")
    parser.add_argument("--prompt", help="非対話モード: プロンプトを 1 回実行して終了")
    parser.add_argument("--workdir", help="作業ディレクトリ (--prompt 時のみ)")
    parser.add_argument("--output-json", dest="output_json", help="結果を JSON で出力")
    parser.add_argument("--model", help="使用モデルを上書き")
    parser.add_argument("--client", help="クライアント種別を上書き (ollama / openai)")
    parser.add_argument("--base-url", dest="base_url", help="API ベース URL を上書き")
    args = parser.parse_args()

    if args.prompt:
        sys.exit(run_oneshot(
            args.prompt, args.workdir, args.output_json, args.model,
            client_override=args.client,
            base_url_override=args.base_url,
        ))
    else:
        from tui import run
        run()
