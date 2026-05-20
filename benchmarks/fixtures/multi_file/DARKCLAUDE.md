# Project Conventions

This project implements a small API with a separate handler layer and tests.

- `src/api.py`: core API functions (data access and manipulation logic)
- `src/handlers.py`: handler functions that call into `api.py` and format responses
- `tests/test_api.py`: pytest tests covering both the API and handler layers

Changes that affect a function's name or signature typically need to be reflected in all three files.
