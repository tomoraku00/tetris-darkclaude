# multi_file

複数ファイルにまたがる変更タスク (T04) 用。

## ファイル構成

- src/api.py: API 実装 (関数定義)
- src/handlers.py: ハンドラ (api.py を呼ぶ)
- tests/test_api.py: pytest テスト

## 作業方針

変更前に全ファイルを読む。呼び出し箇所を全て確認してから str_replace で各ファイルを修正。
最後に pytest で確認。

## 例

ユーザー: get_user を fetch_user にリネーム。呼び出し元も更新。
応答:
read_file(src/api.py)
read_file(src/handlers.py)
read_file(tests/test_api.py)
str_replace(src/api.py, "def get_user", "def fetch_user")
str_replace(src/handlers.py, "get_user(", "fetch_user(")
str_replace(tests/test_api.py, "get_user(", "fetch_user(")
bash(python -m pytest tests/) → 全通過
完了。
