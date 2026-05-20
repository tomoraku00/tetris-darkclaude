# Project Conventions

This project contains a date parsing utility and its test suite.

- `utils.py`: contains `parse_date(date_str)`, which accepts date strings in three formats (YYYY-MM-DD, MM/DD/YYYY, DD.MM.YYYY) and returns a `datetime.date`; currently implemented with chained `if/elif` using `re.match` and `strptime`
- `test_utils.py`: pytest tests covering all three formats and edge cases; the full test suite must pass after any refactoring

The goal of refactoring is to improve readability without changing behavior. The existing test suite defines the contract precisely.
