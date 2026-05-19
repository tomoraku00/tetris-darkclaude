"""プロセッサパイプライン"""
from processors.text_processor import TextProcessor
from processors.csv_processor import CsvProcessor
from processors.json_processor import JsonProcessor
from processors.xml_processor import XmlProcessor
from processors.binary_processor import BinaryProcessor


_REGISTRY = {
    "text": TextProcessor,
    "csv": CsvProcessor,
    "json": JsonProcessor,
    "xml": XmlProcessor,
    "binary": BinaryProcessor,
}


def run_pipeline(data_type: str, data: str, config: dict | None = None) -> dict:
    """指定タイプのプロセッサでデータを処理する"""
    if data_type not in _REGISTRY:
        return {"ok": False, "errors": [f"unknown type: {data_type}"]}
    cls = _REGISTRY[data_type]
    processor = cls(config or {})
    return processor.process(data)
