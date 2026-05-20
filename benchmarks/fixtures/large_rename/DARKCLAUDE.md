# large_rename

大規模クロスファイルリネームタスク (T11) 用。

## ファイル構成

- core/base.py: DataProvider クラス (→ DataSource にリネーム対象)
- core/middleware.py: ミドルウェア
- providers/: cache.py, sql_provider.py 等
- handlers/: ハンドラ群
- tests/: pytest テスト群
- conftest.py: pytest 設定

## 注意点

providers/cache.py ↔ core/middleware.py 間に循環依存がある。
リネーム後に cache.py の middleware import を遅延 import にして解消すること。

## 作業方針

glob(**/*.py) → 全ファイル把握
各ファイルを read_file して DataProvider の出現箇所を確認
str_replace で全ファイルを DataSource に変更
循環依存を遅延 import で解消
bash(python -m pytest tests/) → 全通過確認
bash(python -c "import providers") → 循環依存なし確認。
