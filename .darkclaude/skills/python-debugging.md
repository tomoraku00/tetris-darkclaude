---
name: python-debugging
description: Python のバグ修正手順
keywords: [debug, error, traceback, fix, bug, エラー, デバッグ]
---
## Python デバッグ手順

1. read_file でエラー確認
2. トレースバック最終行に集中
3. str_replace で最小修正
4. py_compile で検証

### よくあるパターン
- IndentationError: スペース4つに統一
- ImportError: モジュール名・パス確認
- TypeError: 型変換 str()/int() を検討
