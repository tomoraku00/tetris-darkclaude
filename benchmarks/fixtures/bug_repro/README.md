# バグレポート: flatten_nested の depth 引数が機能しない

## 症状

`flatten_nested` 関数の `depth` 引数を指定しても、無視されて完全フラット化される。

```python
from list_utils import flatten_nested

# 期待: [1, 2, [3, 4], 5]  (depth=1 なので 1 段階のみ展開)
# 実際: [1, 2, 3, 4, 5]   (depth 指定が無視されて完全フラット)
result = flatten_nested([1, [2, [3, 4]], 5], depth=1)
print(result)
```

## 再現手順

1. `list_utils.py` をインポート
2. `flatten_nested([1, [2, [3, 4]], 5], depth=1)` を呼び出す
3. 期待値 `[1, 2, [3, 4], 5]` ではなく `[1, 2, 3, 4, 5]` が返る

## 期待動作

- `depth=-1`（デフォルト）: 完全フラット
- `depth=0`: フラット化なし（元のリストをそのまま返す）
- `depth=1`: 1 段階のみ展開（ネストしたリストの直下の要素は展開、それ以上はしない）
- `depth=2`: 2 段階展開

## 備考

`depth=0` の場合は正しく動作する（`if depth == 0: return list(lst)` が機能するため）。
