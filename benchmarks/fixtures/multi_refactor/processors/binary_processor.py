"""バイナリファイル処理（Base64 エンコード文字列を受け取る）"""
import base64
import hashlib


class BinaryProcessor:
    def __init__(self, config: dict):
        self.config = config
        self.hash_algo = config.get("hash_algo", "sha256")
        self._errors = []

    def validate(self, data: str) -> bool:
        if not isinstance(data, str):
            self._errors.append("data must be a string")
            return False
        if len(data) == 0:
            self._errors.append("data is empty")
            return False
        try:
            base64.b64decode(data, validate=True)
        except Exception:
            self._errors.append("data is not valid base64")
            return False
        return True

    def process(self, data: str) -> dict:
        if not self.validate(data):
            return {"ok": False, "errors": self._errors.copy()}
        result = self._transform(data)
        return {"ok": True, "result": self._format_output(result)}

    def _transform(self, data: str) -> bytes:
        return base64.b64decode(data)

    def _format_output(self, result: bytes) -> dict:
        h = hashlib.new(self.hash_algo, result).hexdigest()
        return {
            "type": "binary",
            "size_bytes": len(result),
            "hash_algo": self.hash_algo,
            "hash": h,
        }

    def get_errors(self) -> list:
        return self._errors.copy()
