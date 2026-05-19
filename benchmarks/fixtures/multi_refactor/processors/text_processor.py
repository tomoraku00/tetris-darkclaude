"""テキストファイル処理"""


class TextProcessor:
    def __init__(self, config: dict):
        self.config = config
        self.encoding = config.get("encoding", "utf-8")
        self._errors = []

    def validate(self, data: str) -> bool:
        if not isinstance(data, str):
            self._errors.append("data must be a string")
            return False
        if len(data) == 0:
            self._errors.append("data is empty")
            return False
        return True

    def process(self, data: str) -> dict:
        if not self.validate(data):
            return {"ok": False, "errors": self._errors.copy()}
        result = self._transform(data)
        return {"ok": True, "result": self._format_output(result)}

    def _transform(self, data: str) -> str:
        lines = data.splitlines()
        lines = [ln.strip() for ln in lines if ln.strip()]
        return "\n".join(lines)

    def _format_output(self, result: str) -> dict:
        return {
            "type": "text",
            "lines": result.splitlines(),
            "line_count": len(result.splitlines()),
        }

    def get_errors(self) -> list:
        return self._errors.copy()
