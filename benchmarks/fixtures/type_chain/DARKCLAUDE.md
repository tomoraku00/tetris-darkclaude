# Project Conventions

This project contains a geometry module and its test suite.

- `shapes.py`: `Shape` class hierarchy with concrete subclasses; includes factory functions and a search function; currently has type annotation errors under `mypy --strict`
- `test_shapes.py`: 8 pytest tests covering shape creation, area calculation, and the factory/search functions

The goal is to make `mypy --strict shapes.py` pass with 0 errors while keeping all 8 tests green. Running mypy first gives a full list of what needs fixing.
