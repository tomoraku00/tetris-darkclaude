# Project Conventions

This project implements a small REST-style API with an in-memory data store.

- `api.py`: data access functions operating on `_USERS` and `_POSTS` dicts; each function takes typed arguments and returns data or `None`
- `handlers.py`: handler functions that call `api.py` and return `{"status": <int>, "data": ...}` response dicts
- `tests/test_api.py`: pytest tests for both layers; existing tests define the expected response format

New functionality should follow the patterns already established in `api.py` and `handlers.py`.
