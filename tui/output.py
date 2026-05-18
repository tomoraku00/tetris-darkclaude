import threading
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.document import Document


class OutputBuffer:
    """Thread-safe wrapper around a prompt_toolkit Buffer for TUI output display."""

    def __init__(self) -> None:
        self._buf = Buffer(name="output", read_only=False)
        self._lock = threading.Lock()

    @property
    def buffer(self) -> Buffer:
        return self._buf

    def append(self, text: str) -> None:
        with self._lock:
            new_text = self._buf.text + text
            self._buf.set_document(Document(new_text, cursor_position=len(new_text)))

    def clear(self) -> None:
        with self._lock:
            self._buf.set_document(Document("", cursor_position=0))
