"""重複・共通要素検索（意図的に非効率な実装）"""


def find_duplicates(items: list) -> list:
    """リスト中の重複要素を返す（O(n^2) 実装）"""
    duplicates = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            if items[i] == items[j] and items[i] not in duplicates:
                duplicates.append(items[i])
    return sorted(duplicates)


def find_common_elements(list_a: list, list_b: list) -> list:
    """2 つのリストの共通要素を返す（O(n*m) 実装）"""
    common = []
    for item in list_a:
        if item in list_b and item not in common:
            common.append(item)
    return sorted(common)


def count_unique(items: list) -> int:
    """ユニーク要素数を返す（O(n^2) 実装）"""
    unique = []
    for item in items:
        if item not in unique:
            unique.append(item)
    return len(unique)
