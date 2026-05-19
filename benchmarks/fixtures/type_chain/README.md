# 型エラー修正

shapes.py は `mypy --strict` で 30+ エラーがあります。
全ての型エラーを修正してください。

## 現状確認

```bash
python -m mypy --strict shapes.py
```

上記を実行すると多数のエラーが出ます。

## 要件

- `mypy --strict shapes.py` で 0 エラー
- `pytest test_shapes.py` で全テスト通過
- `Any` 型を使わない
- 型注釈は明示的に (`Optional`, `Union`, `list[Shape]` など)

## ヒント

- `Shape` は `ABC` を継承すべき
- `area()` の戻り値は `float`
- `find_largest` の戻り値は `Optional[Shape]`
- `make_shape` の戻り値は `Optional[Shape]`
- `*args` の型は `float` で渡されることを前提にしてよい
