# deep_bug

テスト失敗バグの修正タスク (T07) 用。

## ファイル構成

- date_range.py: DateRange クラス (境界値バグあり)
- test_date_range.py: pytest テスト (8 件中 4 件が失敗)

## バグの概要

`_is_valid_date` で `self.start <= d < self.end` (end 排他) になっているため、
end 当日が範囲外と判定される。`self.start <= d <= self.end` (end 包括) に修正する。

## 作業方針

bash(python -m pytest test_date_range.py) → 失敗確認
read_file(date_range.py) → バグ箇所特定
str_replace で修正 → pytest 全通過確認。
