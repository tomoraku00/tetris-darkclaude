# Project Conventions

This project contains a date range utility and its test suite.

- `date_range.py`: `DateRange` class with an `_is_valid_date(d)` method for checking whether a date falls within the range; also exposes iteration and containment logic
- `test_date_range.py`: pytest tests covering boundary values and range membership; some tests are currently failing

Running the test suite is a good first step to understand which behaviors are broken.
