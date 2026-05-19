# Race Condition バグ

`AsyncCounter.increment` に race condition があります。
100 並列で実行すると、結果が 100 にならないことがあります。

## 症状

```python
c = AsyncCounter()
result = asyncio.run(c.run_concurrent(100))
print(result)  # 100 のはずが 1 になることがある
```

## 原因

`increment` 内で `read → sleep → write` の間に他のコルーチンが割り込み、
同じ `current` 値を複数のコルーチンが読み取ってしまう。

## 修正方法

- `asyncio.Lock` を使って `increment` のクリティカルセクションを排他制御する
- または `asyncio.Queue` を使ってシリアルに処理する

## 要件

- `increment(self, delay: float = 0.001)` のシグネチャは変えない
- `run_concurrent(self, n: int = 100)` のシグネチャは変えない
- test_counter.py が 20 回連続で通過すること
