# Project Conventions

This project contains an async counter and a concurrent test suite.

- `counter.py`: `AsyncCounter` class with an `increment()` coroutine and a `value` property; designed for use with `asyncio`
- `test_counter.py`: pytest-asyncio tests that run multiple coroutines concurrently to verify correctness under load; the test suite runs 20 iterations
- `README.md`: describes the observed bug and the expected correct behavior

Run the tests first to observe the failure, then read the source and README to understand the root cause.
