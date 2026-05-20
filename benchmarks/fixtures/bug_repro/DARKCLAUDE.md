# bug_repro

バグ再現・修正タスク (T10) 用。

## ファイル構成

- list_utils.py: flatten_nested 関数 (depth 引数バグあり)
- README.md: バグの詳細・再現手順・期待動作

## バグの概要

flatten_nested の depth 引数が内部再帰呼び出しに渡されていないため、
depth 指定が無視されて完全フラット化される。

## 作業方針

read_file(README.md) → バグ仕様確認
read_file(list_utils.py) → 原因特定
write_file(test_list_utils.py) → テスト作成 (depth=0/1/2/-1 のケース)
str_replace(list_utils.py) → depth を再帰呼び出しに渡すよう修正
bash(python -m pytest test_list_utils.py) → 全通過確認。
