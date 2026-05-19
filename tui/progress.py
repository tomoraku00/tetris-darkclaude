"""進捗インジケータ — OSC 9;4 (ターミナルタブ) + ITaskbarList3 (タスクバーアイコン) の両対応。"""
import sys
from . import taskbar


def _osc94(state: int, value: int = 0) -> None:
    """OSC 9;4 でターミナルタブに進捗を表示する。

    prompt_toolkit の full_screen モードでは sys.stdout がバッファされるため
    sys.__stdout__ を使って実ターミナルに直接書き込む。
    """
    seq = f"\x1b]9;4;{state};{value}\x07"
    try:
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
    """作業中: タブ (橙 indeterminate) + タスクバーアイコン (橙)。"""
    _osc94(3)
    taskbar.working()


def done() -> None:
    """完了: タブ (緑 100%) + タスクバーアイコン (緑)。"""
    _osc94(1, 100)
    taskbar.done()


def error() -> None:
    """エラー: タブ (赤) + タスクバーアイコン (赤)。"""
    _osc94(2, 100)
    taskbar.error()


def clear() -> None:
    """通常状態に戻す。"""
    _osc94(0, 0)
    taskbar.clear()
