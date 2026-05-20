# Project Conventions

This project contains a search/set-operation utility and performance tooling.

- `finder.py`: functions for finding duplicates, common elements, and unique counts across lists; currently uses nested loops
- `test_finder.py`: pytest tests verifying correctness of each function
- `benchmark.py`: standalone timing script; run it to measure actual performance before and after changes

Correctness (tests passing) takes priority. Performance measurements come from `benchmark.py`.
