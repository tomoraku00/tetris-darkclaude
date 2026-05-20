# Project Conventions

This project implements a multi-format processor pipeline.

- `pipeline.py`: pipeline entry point; manages processor registration via `_REGISTRY` and dispatches input to the appropriate processor by format
- `processors/`: one processor module per format — `text_processor.py`, `csv_processor.py`, `json_processor.py`, `xml_processor.py`, `binary_processor.py`

Each processor follows a similar structure. Use `glob` to survey all files before reading individual processors.
