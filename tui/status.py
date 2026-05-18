import time
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.application.current import get_app


def make_status_fn(state: dict, start_time: float):
    """ステータスライン用の get_status() クロージャを生成して返す。"""

    def get_status() -> FormattedText:
        elapsed = int(time.time() - start_time)
        mins = elapsed // 60
        secs = elapsed % 60

        model = state.get("model", "?")
        phase = "A6 stabilization"
        thinking = state.get("thinking", "")

        try:
            width = get_app().output.get_size().columns
        except Exception:
            width = 80

        right_text = f"⏱ {mins}m {secs:02d}s "

        left_parts: list[tuple[str, str]] = [
            ("class:status.value", f" {model}"),
            ("class:status", " · "),
            ("class:status.mode", f"Phase {phase}"),
        ]
        if thinking:
            left_parts += [
                ("class:status", " · "),
                ("class:thinking", thinking),
            ]

        # 左右の文字数を概算してパディング
        left_len = sum(len(t) for _, t in left_parts)
        right_len = len(right_text)
        pad = max(1, width - left_len - right_len)

        return FormattedText(
            left_parts
            + [("class:status", " " * pad)]
            + [("class:status", "⏱ ")]
            + [("class:status.value", f"{mins}m {secs:02d}s ")]
        )

    return get_status
