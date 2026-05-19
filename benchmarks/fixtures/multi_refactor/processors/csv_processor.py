"""CSV ファイル処理"""
import csv
import io


class CsvProcessor:
    def __init__(self, config: dict):
        self.config = config
        self.delimiter = config.get("delimiter", ",")
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

    def _transform(self, data: str) -> list:
        reader = csv.reader(io.StringIO(data), delimiter=self.delimiter)
        rows = [row for row in reader if any(cell.strip() for cell in row)]
        return rows

    def _format_output(self, result: list) -> dict:
        if not result:
            return {"type": "csv", "headers": [], "rows": [], "row_count": 0}
        headers = result[0]
        rows = result[1:]
        return {
            "type": "csv",
            "headers": headers,
            "rows": rows,
            "row_count": len(rows),
        }

    def get_errors(self) -> list:
        return self._errors.copy()
