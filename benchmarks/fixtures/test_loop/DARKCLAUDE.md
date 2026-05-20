# test_loop

テスト失敗を修正するタスク (T05) 用。

## ファイル構成

- calculator.py: 電卓モジュール (add が未実装、pass のまま)
- test_calculator.py: pytest テスト

## 作業方針

read_file(test_calculator.py) でテスト仕様確認 → read_file(calculator.py) で現状確認 →
str_replace で実装 → pytest で通過確認。

## 例

ユーザー: add を実装してテストを通してください
応答:
read_file(test_calculator.py) → `assert add(2, 3) == 5` を確認
str_replace(calculator.py, "    pass", "    return a + b")
bash(python -m pytest test_calculator.py) → 全通過
完了。
