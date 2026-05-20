# Project Conventions

This project is a multi-module Python codebase with a provider/handler architecture.

- `core/base.py`: defines the central base class used throughout the project
- `core/middleware.py`: middleware layer that imports from `core/base.py` and `providers/`
- `providers/`: individual provider implementations (`cache.py`, `sql_provider.py`, etc.); some import from `core/middleware.py`
- `handlers/`: handler modules that import from `providers/`
- `tests/`: pytest test suite
- `conftest.py`: shared pytest fixtures

Note: there is a circular import between `providers/cache.py` and `core/middleware.py`. Use `glob` to survey all files before making changes.
