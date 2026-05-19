"""ネストしたリストのユーティリティ"""


def flatten_nested(lst: list, depth: int = -1) -> list:
    """ネストしたリストをフラット化する。

    Args:
        lst: フラット化するリスト
        depth: フラット化する深さ。-1 は無限（完全フラット）、
               0 はフラット化なし、1 は 1 段階のみ展開。

    Examples:
        >>> flatten_nested([1, [2, [3, 4]], 5])
        [1, 2, 3, 4, 5]
        >>> flatten_nested([1, [2, [3, 4]], 5], depth=1)
        [1, 2, [3, 4], 5]
    """
    if depth == 0:
        return list(lst)
    result = []
    for item in lst:
        if isinstance(item, list):
            # バグ: depth を 1 減らさずにそのまま渡している
            result.extend(flatten_nested(item, depth))
        else:
            result.append(item)
    return result
