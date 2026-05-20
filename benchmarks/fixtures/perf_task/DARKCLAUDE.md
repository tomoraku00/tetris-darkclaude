# perf_task

パフォーマンス改善タスク (T08) 用。

## ファイル構成

- finder.py: 重複・共通要素検索 (O(n^2) 実装、最適化対象)
- test_finder.py: pytest テスト
- benchmark.py: 速度測定スクリプト

## 作業方針

bash(python benchmark.py) → 現状確認
read_file(finder.py) → ボトルネック特定 (ネストループ)
set を使って O(n) に改善 → pytest 確認 → benchmark 再実行。

## 改善方針

- find_duplicates: `seen = set()` でループ 1 回に
- find_common_elements: `set(list_b)` で内側ループを O(1) に
- count_unique: `return len(set(items))` で完結

目標: n=2500 で合計 0.5 秒以内。
