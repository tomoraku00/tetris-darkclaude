# race_condition

非同期 race condition 修正タスク (T12) 用。

## ファイル構成

- counter.py: AsyncCounter クラス (race condition あり)
- test_counter.py: テスト (20 回連続実行で全通過が条件)
- README.md: バグの詳細・修正方法

## バグの概要

increment 内で `read → await sleep → write` の間に他のコルーチンが割り込み、
同じ current 値を複数のコルーチンが読んでしまう。

## 修正方法

`__init__` に `self._lock = asyncio.Lock()` を追加し、
increment 内を `async with self._lock:` で囲む。

## 作業方針

read_file(counter.py) → 問題箇所確認
str_replace で asyncio.Lock を追加
bash(python -m pytest test_counter.py -v) → 通過確認 (20 回連続テスト)。
