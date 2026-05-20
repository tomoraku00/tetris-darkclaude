# type_chain

mypy 型エラー修正タスク (T13) 用。

## ファイル構成

- shapes.py: Shape クラス群 (mypy --strict で 30+ エラー)
- test_shapes.py: pytest テスト (8 件)

## 要件

- mypy --strict shapes.py で 0 エラー
- pytest test_shapes.py で全テスト通過
- Any 型は使わない

## 作業方針

read_file(shapes.py) → 現状確認
bash(python -m mypy --strict shapes.py) → エラー一覧確認
str_replace でエラーを修正 (ABC 継承、Optional[Shape]、float 注釈など)
bash(python -m pytest test_shapes.py) → テスト確認。

## ヒント

- Shape: ABC を継承、area() の戻り値は float
- find_largest の戻り値: Optional[Shape]
- make_shape の戻り値: Optional[Shape]
- *args は float 前提で型注釈
