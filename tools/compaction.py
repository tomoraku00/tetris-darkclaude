"""E7: Auto-Compaction — 会話履歴が context 上限に近づいたら自動要約圧縮。

戦略:
  1. estimate_tokens() で履歴のトークン数を簡易推定
  2. 閾値 (デフォルト 70%) を超えたら compact_history() を呼ぶ
  3. 最新 N メッセージは保持、古い中間部分を LLM で要約してまとめる
  4. 圧縮内容を data/compaction_log/ に保存 (デバッグ用)
"""
import json
from datetime import datetime
from pathlib import Path

CONTEXT_LIMIT = 32768  # トークン上限 (qwen3 の実際の上限に合わせて調整可)


# ---- トークン推定 ----

def estimate_tokens(text: str) -> int:
    """簡易トークン数推定。英数字 4 文字 ≈ 1 トークン、日本語 1.5 文字 ≈ 1 トークン。"""
    ascii_count = sum(1 for c in text if c.isascii())
    non_ascii_count = len(text) - ascii_count
    return ascii_count // 4 + int(non_ascii_count / 1.5)


def estimate_history_tokens(history: list[dict]) -> int:
    """メッセージリスト全体のトークン数を推定。"""
    total = 0
    for msg in history:
        content = msg.get("content") or ""
        if isinstance(content, list):
            content = " ".join(str(c) for c in content)
        total += estimate_tokens(str(content))
    return total


def should_compact(history: list[dict], threshold: float = 0.7) -> bool:
    """閾値超えなら True。"""
    return estimate_history_tokens(history) > CONTEXT_LIMIT * threshold


# ---- 圧縮実行 ----

def compact_history(
    history: list[dict],
    client,
    model: str,
    recent_n: int = 5,
) -> list[dict]:
    """会話履歴を圧縮。最新 recent_n メッセージは保持し、古い部分を要約に置換。

    LLM 要約が失敗した場合はフォールバック: 単純切り捨て + 通知メッセージ。
    """
    if len(history) <= recent_n:
        return history  # 圧縮するものがない

    recent = history[-recent_n:]
    middle = history[:-recent_n]

    # 中間部分を LLM で要約
    summary = _summarize(middle, client, model)

    summary_msg = {
        "role": "system",
        "content": f"## Earlier conversation summary\n\n{summary}",
    }
    return [summary_msg] + recent


def _summarize(messages: list[dict], client, model: str) -> str:
    """中間メッセージを LLM で要約。失敗したらフォールバック文字列を返す。"""
    middle_text = "\n".join(
        f"{msg['role']}: {str(msg.get('content', ''))[:500]}"
        for msg in messages
    )
    prompt = (
        "以下の会話履歴を 300 字以内で要約してください。"
        "重要なファイルパス、決定事項、未解決の問題を漏らさないでください。\n\n"
        + middle_text
    )
    try:
        response = client.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            tools=[],
            think=False,
        )
        text = response["message"].get("content", "").strip()
        if text:
            return text
    except Exception:
        pass
    # フォールバック: メッセージ数だけ記録
    return f"(要約取得失敗。{len(messages)} 件のメッセージが省略されました。)"


# ---- ログ保存 ----

def save_compaction_log(original: list[dict], compressed: list[dict]) -> Path:
    """圧縮ログを data/compaction_log/ に JSON で保存。"""
    log_dir = Path("data") / "compaction_log"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    log_file.write_text(
        json.dumps(
            {
                "original_count": len(original),
                "compressed_count": len(compressed),
                "original": original,
                "compressed": compressed,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return log_file
