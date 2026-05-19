"""XML ファイル処理"""
import xml.etree.ElementTree as ET


class XmlProcessor:
    def __init__(self, config: dict):
        self.config = config
        self.root_tag = config.get("root_tag", "root")
        self._errors = []

    def validate(self, data: str) -> bool:
        if not isinstance(data, str):
            self._errors.append("data must be a string")
            return False
        if len(data) == 0:
            self._errors.append("data is empty")
            return False
        try:
            ET.fromstring(data)
        except ET.ParseError as e:
            self._errors.append(f"invalid XML: {e}")
            return False
        return True

    def process(self, data: str) -> dict:
        if not self.validate(data):
            return {"ok": False, "errors": self._errors.copy()}
        result = self._transform(data)
        return {"ok": True, "result": self._format_output(result)}

    def _transform(self, data: str) -> ET.Element:
        return ET.fromstring(data)

    def _format_output(self, result: ET.Element) -> dict:
        def elem_to_dict(elem):
            d = {"tag": elem.tag, "text": (elem.text or "").strip(), "children": []}
            for child in elem:
                d["children"].append(elem_to_dict(child))
            return d

        return {
            "type": "xml",
            "root": elem_to_dict(result),
            "child_count": len(list(result)),
        }

    def get_errors(self) -> list:
        return self._errors.copy()
