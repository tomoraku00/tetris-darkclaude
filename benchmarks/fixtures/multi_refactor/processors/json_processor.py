"""JSON ファイル処理"""
import json


class JsonProcessor:
    def __init__(self, config: dict):
        self.config = config
        self.indent = config.get("indent", 2)
        self._errors = []

    def validate(self, data: str) -> bool:
        if not isinstance(data, str):
            self._errors.append("data must be a string")
            return False
        if len(data) == 0:
            self._errors.append("data is empty")
            return False
        try:
            json.loads(data)
        except json.JSONDecodeError as e:
            self._errors.append(f"invalid JSON: {e}")
            return False
        return True

    def process(self, data: str) -> dict:
        if not self.validate(data):
            return {"ok": False, "errors": self._errors.copy()}
        result = self._transform(data)
        return {"ok": True, "result": self._format_output(result)}

    def _transform(self, data: str) -> object:
        parsed = json.loads(data)
        return parsed

    def _format_output(self, result: object) -> dict:
        return {
            "type": "json",
            "data": result,
            "pretty": json.dumps(result, indent=self.indent, ensure_ascii=False),
        }

    def get_errors(self) -> list:
        return self._errors.copy()
