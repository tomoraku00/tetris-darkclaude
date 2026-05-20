# syntax_error

Python 構文エラーを修正するタスク (T02) 用。

## ファイル構成

- bug.py: 構文エラーを含む Python ファイル

## 作業方針

read_file(bug.py) で内容確認 → str_replace で修正 → py_compile で検証。

## 例

ユーザー: bug.py に syntax error があります。修正してください。
応答:
read_file(bug.py) → `if x = 1:` を発見 (代入を比較演算子で修正)
str_replace(bug.py, "if x = 1:", "if x == 1:")
bash(python -m py_compile bug.py) → エラーなし
修正完了。
