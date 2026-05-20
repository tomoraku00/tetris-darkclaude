# api_extend

REST 風 API 拡張タスク (T09) 用。

## ファイル構成 (api_extend/ 内)

- api.py: ユーザー・投稿 API (_USERS, _POSTS 辞書ベース)
- handlers.py: ハンドラ ({"status": 200, "data": ...} 形式で返す)
- tests/test_api.py: pytest テスト

## 追加する関数

api.py:
- `get_user_posts(user_id: int) -> list[dict] | None`: _POSTS から user_id で絞り込み
- `delete_user(user_id: int) -> bool`: _USERS から削除

handlers.py:
- `handle_get_user_posts(user_id)`: status 200/404
- `handle_delete_user(user_id)`: status 200/404

tests/: 新テスト 3 件以上 (既存 3 件も継続通過させる)

## 作業方針

read_file(api_extend/api.py) → read_file(api_extend/handlers.py) →
既存パターンを参考に str_replace で追加 → pytest で確認。
