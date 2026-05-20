# Project Conventions

This is a small Python project modeled after a CLI coding assistant.

- `main.py`: entry point; calls `tui.run()`
- `prompts.py`: system prompt string definitions
- `clients/`: LLM client abstraction layer; contains one or more client implementations
- `tools/`: tool implementations (read_file, write_file, bash, glob, str_replace)
- `tui/`: TUI implementation; key files include app.py (main loop), chat.py (LLM turn), output.py (display buffer), banner.py (startup screen)

The `tui/` directory contains the bulk of the logic. `clients/` and `tools/` each hold multiple Python files.

When describing structure, cover all four directories and explain each one's role.
