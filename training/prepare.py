"""
prepare.py - DarkClaude 会話ログ（JSONL）→ ChatML 訓練データ変換

Usage:
    python prepare.py [--input ../data/conversations] [--output prepared]
"""
import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)


def strip_think(text: str) -> str:
    return THINK_RE.sub("", text).strip()


def parse_session(path: Path) -> tuple[dict, list[dict]]:
    """JSONL ファイルを 1 行 1 イベントとして読み込む。"""
    events: list[dict] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    session_info: dict = {}
    for ev in events:
        if ev.get("type") == "session_start":
            session_info = ev
            break

    end_reason = ""
    for ev in reversed(events):
        if ev.get("type") == "session_end":
            end_reason = ev.get("reason", "")
            break
    session_info["_end_reason"] = end_reason

    return session_info, events


def reconstruct_turns(events: list[dict]) -> list[dict]:
    """
    イベント列をターン（user_message → assistant_message）単位に再構成する。
    各ターン dict:
      user_content: str
      messages: list  # ターン内の ChatML メッセージ（user/assistant/tool）
      has_think: bool
      has_user_denied: bool
      is_complete: bool
      final_content: str | None
    """
    turns: list[dict] = []
    current: dict | None = None

    for ev in events:
        t = ev.get("type")

        if t == "user_message":
            current = {
                "user_content": ev.get("content", ""),
                "messages": [],
                "has_think": False,
                "has_user_denied": False,
                "is_complete": False,
                "final_content": None,
            }

        elif t == "llm_call" and current is not None:
            resp = ev.get("response")
            if not isinstance(resp, dict):
                continue
            content = resp.get("content") or ""
            tool_calls = resp.get("tool_calls")

            if "<think>" in content:
                current["has_think"] = True

            if tool_calls:
                # 中間 LLM 呼び出し（ツール呼び出しあり）
                current["messages"].append({
                    "role": "assistant",
                    "content": content,
                    "tool_calls": tool_calls,
                })

        elif t == "tool_result" and current is not None:
            if ev.get("is_user_denied"):
                current["has_user_denied"] = True
            current["messages"].append({
                "role": "tool",
                "content": ev.get("content", ""),
                "name": ev.get("tool", ""),
            })

        elif t == "assistant_message" and current is not None:
            content = ev.get("content") or ""
            if "<think>" in content:
                current["has_think"] = True
            current["final_content"] = content
            current["messages"].append({
                "role": "assistant",
                "content": strip_think(content),
            })
            current["is_complete"] = True
            turns.append(current)
            current = None

    return turns


def build_samples(session_info: dict, turns: list[dict]) -> list[dict]:
    """
    ターンリスト → 訓練サンプルリスト（過去ターンを context として前置き）
    フィルタ: USER_DENIED 除外 / 不完全ターン除外 / 空応答除外
    """
    system_prompt = session_info.get("system_prompt", "")
    end_reason = session_info.get("_end_reason", "")
    samples: list[dict] = []
    ctx_messages: list[dict] = []  # 蓄積済み context

    for i, turn in enumerate(turns):
        # USER_DENIED ターン除外（context 蓄積もスキップ）
        if turn["has_user_denied"]:
            continue

        # 不完全ターン除外
        if not turn["is_complete"]:
            continue

        # ctrl_c / eof で終了したセッションの最終ターンを除外
        is_last = i == len(turns) - 1
        if is_last and end_reason in ("ctrl_c", "eof"):
            continue

        # 空応答除外
        final = (turn["final_content"] or "").strip()
        if not final:
            continue

        # サンプル構築
        messages: list[dict] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.extend(ctx_messages)
        messages.append({"role": "user", "content": turn["user_content"]})
        messages.extend(turn["messages"])

        samples.append({"messages": messages, "has_think": turn["has_think"]})

        # 次のターンの context に追加（最終応答のみ、tool ループは省略）
        ctx_messages.append({"role": "user", "content": turn["user_content"]})
        ctx_messages.append({"role": "assistant", "content": strip_think(final)})

    return samples


def prepare(input_dir: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    jsonl_files = sorted(input_dir.glob("*.jsonl"))

    if not jsonl_files:
        print(f"[prepare] 入力ファイルなし: {input_dir}")
        print("[prepare] 出力なし（正常終了）")
        print_stats(0, 0)
        return

    all_samples: list[dict] = []
    total_turns = 0
    reasoning_turns = 0

    for path in jsonl_files:
        session_info, events = parse_session(path)
        turns = reconstruct_turns(events)
        samples = build_samples(session_info, turns)
        for s in samples:
            total_turns += 1
            if s["has_think"]:
                reasoning_turns += 1
        all_samples.extend(samples)

    # 重複除去（messages JSON 文字列で比較）
    seen: set[str] = set()
    deduped: list[dict] = []
    for s in all_samples:
        key = json.dumps(s["messages"], ensure_ascii=False, sort_keys=True)
        if key not in seen:
            seen.add(key)
            deduped.append(s)
    duplicates = len(all_samples) - len(deduped)

    # 出力
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_path = output_dir / f"{timestamp}.jsonl"
    with out_path.open("w", encoding="utf-8") as f:
        for s in deduped:
            f.write(json.dumps({"messages": s["messages"]}, ensure_ascii=False) + "\n")

    print(f"[prepare] 出力: {out_path}")
    print(f"[prepare] サンプル数: {len(deduped)}")
    if duplicates:
        print(f"[prepare] 重複除去: {duplicates} 件")
    print_stats(total_turns, reasoning_turns)


def print_stats(total: int, reasoning: int) -> None:
    print("\n--- reasoning ratio ---")
    print(f"  全ターン数         : {total}")
    print(f"  <think> 含むターン : {reasoning}")
    ratio = reasoning / total * 100 if total > 0 else 0.0
    print(f"  reasoning 比率     : {ratio:.1f}%  (目標 75%)")
    if total > 0:
        dev = ratio - 75.0
        sign = "+" if dev >= 0 else ""
        print(f"  目標比 乖離        : {sign}{dev:.1f}pp")
    print("-----------------------")


def main() -> None:
    parser = argparse.ArgumentParser(description="DarkClaude JSONL → ChatML 変換")
    parser.add_argument("--input", default="../data/conversations",
                        help="入力ディレクトリ (default: ../data/conversations)")
    parser.add_argument("--output", default="prepared",
                        help="出力ディレクトリ (default: prepared)")
    args = parser.parse_args()

    script_dir = Path(__file__).parent.resolve()
    input_dir = (script_dir / args.input).resolve()
    output_dir = (script_dir / args.output).resolve()

    print(f"[prepare] 入力: {input_dir}")
    print(f"[prepare] 出力: {output_dir}")
    prepare(input_dir, output_dir)


if __name__ == "__main__":
    main()
