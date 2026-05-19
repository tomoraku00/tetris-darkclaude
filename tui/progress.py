"""タスクバー進捗インジケータ (OSC 9;4 — Windows Terminal 対応)"""
import sys


def set_progress(state: int, value: int = 0) -> None:
    """OSC 9;4 シーケンスでタスクバーアイコンの進捗を制御する。

    state:
        0 = clear (通常状態)
        1 = normal (green progress)
        2 = error (red)
        3 = indeterminate (working、橙の流れる表示)
        4 = warning (yellow)
    value: 0-100、state=1/2/4 で使用

    prompt_toolkit full_screen 時は sys.stdout がバッファされるため
    sys.__stdout__ を使ってターミナルに直接書き込む。
    """
    seq = f"\x1b]9;4;{state};{value}\x07"
    try:
        # prompt_toolkit の出力バッファをバイパスして実ターミナルへ書き込む
        out = getattr(sys, "__stdout__", None) or sys.stdout
        out.write(seq)
        out.flush()
    except Exception:
        try:
            sys.stdout.write(seq)
            sys.stdout.flush()
        except Exception:
            pass


def working() -> None:
    """作業中表示 (indeterminate、橙)"""
    set_progress(3)


def done() -> None:
    """完了表示 (green 100%)"""
    set_progress(1, 100)


def error() -> None:
    """エラー表示 (red)"""
    set_progress(2, 100)


def clear() -> None:
    """通常状態に戻す"""
    set_progress(0)
