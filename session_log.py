import json
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path


class SessionLog:
    def __init__(
        self,
        enabled: bool,
        base_dir: Path,
        dc_version: str,
        model: str,
        plan_mode: bool,
        think_mode: str,
        system_prompt: str,
    ) -> None:
        self._enabled = enabled
        self._base_dir = base_dir
        self._dc_version = dc_version
        self._model = model
        self._plan_mode = plan_mode
        self._think_mode = think_mode
        self._system_prompt = system_prompt
        self._session_id = secrets.token_hex(4)
        self._file = None
        self._file_path: Path | None = None
        self._dead = False
        if enabled:
            self._open_file()

    def _open_file(self) -> bool:
        try:
            self._base_dir.mkdir(parents=True, exist_ok=True)
            now = datetime.now()
            filename = f"{now.strftime('%Y%m%d-%H%M%S')}_{self._session_id}.jsonl"
            self._file_path = self._base_dir / filename
            self._file = self._file_path.open("a", encoding="utf-8")
            return True
        except Exception as e:
            print(f"[warn] SessionLog: cannot open log file: {e}", file=sys.stderr)
            self._dead = True
            return False

    @staticmethod
    def _ts() -> str:
        now = datetime.now(timezone.utc)
        return now.strftime(f"%Y-%m-%dT%H:%M:%S.{now.microsecond // 1000:03d}Z")

    def _write(self, event: dict) -> None:
        if not self._enabled or self._dead or self._file is None:
            return
        try:
            self._file.write(json.dumps(event, ensure_ascii=False, default=str) + "\n")
            self._file.flush()
        except Exception as e:
            print(f"[warn] SessionLog: write error: {e}", file=sys.stderr)
            self._dead = True

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def file_path(self) -> Path | None:
        return self._file_path

    def toggle(self) -> bool:
        return self.set_enabled(not self._enabled)

    def set_enabled(self, value: bool) -> bool:
        if not value:
            self._enabled = False
            return False
        self._enabled = True
        if self._dead:
            return False
        if self._file is None:
            success = self._open_file()
            if not success:
                self._enabled = False
                return False
        return True

    def update_context(self, *, plan_mode: bool | None = None, think_mode: str | None = None) -> None:
        if plan_mode is not None:
            self._plan_mode = plan_mode
        if think_mode is not None:
            self._think_mode = think_mode

    def close(self, reason: str) -> None:
        if self._file is None:
            return
        self._write({
            "ts": self._ts(),
            "type": "session_end",
            "reason": reason,
            "session_id": self._session_id,
        })
        try:
            self._file.close()
        except Exception:
            pass
        self._file = None

    def session_start(self) -> None:
        self._write({
            "ts": self._ts(),
            "type": "session_start",
            "dc_version": self._dc_version,
            "model": self._model,
            "plan_mode": self._plan_mode,
            "think_mode": self._think_mode,
            "logging_enabled": self._enabled,
            "system_prompt": self._system_prompt,
            "session_id": self._session_id,
        })

    def user_message(self, content: str) -> None:
        self._write({"ts": self._ts(), "type": "user_message", "content": content})

    def llm_call(self, request_messages: list, response: object, latency_ms: int) -> None:
        self._write({
            "ts": self._ts(),
            "type": "llm_call",
            "request_messages": request_messages,
            "response": response,
            "latency_ms": latency_ms,
            "plan_mode": self._plan_mode,
            "think_mode": self._think_mode,
        })

    def tool_call(self, tool: str, args: dict) -> None:
        self._write({"ts": self._ts(), "type": "tool_call", "tool": tool, "args": args})

    def approval(self, tool: str, args: dict, decision: str) -> None:
        self._write({"ts": self._ts(), "type": "approval", "tool": tool, "args": args, "decision": decision})

    def tool_result(self, tool: str, args: dict, content: str, is_user_denied: bool) -> None:
        self._write({
            "ts": self._ts(),
            "type": "tool_result",
            "tool": tool,
            "args": args,
            "content": content,
            "is_user_denied": is_user_denied,
        })

    def assistant_message(self, content: str, total_latency_ms: int) -> None:
        self._write({
            "ts": self._ts(),
            "type": "assistant_message",
            "content": content,
            "total_latency_ms": total_latency_ms,
        })
