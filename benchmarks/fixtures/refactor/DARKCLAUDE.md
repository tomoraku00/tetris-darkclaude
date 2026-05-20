# refactor

関数リファクタリングタスク (T03) 用。

## ファイル構成

- utils.py: リファクタリング対象 (parse_date 関数)
- test_utils.py: pytest テスト

## 作業方針

read_file(utils.py) で現状確認 → str_replace で可読性を改善 → pytest で確認。
機能は変えない。変数名・早期 return・コメント整理などを行う。

## 例

ユーザー: parse_date を refactor して
応答:
read_file(utils.py) → 現状確認
str_replace(utils.py, ...旧コード..., ...改善版...)
bash(python -m pytest test_utils.py) → 全テスト通過
完了。
