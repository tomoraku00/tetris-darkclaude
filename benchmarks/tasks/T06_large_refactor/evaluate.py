"""T06 評価: BaseProcessor 抽出 + 継承 + pipeline 動作"""
import subprocess
import sys
from pathlib import Path


def evaluate(workdir: Path, result: dict) -> float:
    proc_dir = workdir / "multi_refactor" / "processors"
    score = 0.0

    # BaseProcessor が作成されているか (0.25)
    base_file = proc_dir / "base_processor.py"
    if not base_file.exists():
        return 0.0
    base_src = base_file.read_text(encoding="utf-8")
    has_abstractmethod = "abstractmethod" in base_src
    has_abc = "ABC" in base_src or "ABCMeta" in base_src
    if has_abstractmethod and has_abc:
        score += 0.25

    # 各プロセッサが BaseProcessor を継承しているか (各 0.1、計 0.50)
    processor_files = [
        "text_processor.py",
        "csv_processor.py",
        "json_processor.py",
        "xml_processor.py",
        "binary_processor.py",
    ]
    for fname in processor_files:
        src_path = proc_dir / fname
        if src_path.exists():
            src = src_path.read_text(encoding="utf-8")
            if "BaseProcessor" in src:
                score += 0.10

    # pipeline.py が実際に動くか (0.25)
    pipeline_file = workdir / "multi_refactor" / "pipeline.py"
    if pipeline_file.exists():
        test_script = """
import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from pipeline import run_pipeline
r = run_pipeline("text", "hello world")
assert r["ok"], f"text failed: {r}"
r2 = run_pipeline("json", '{"key": "val"}')
assert r2["ok"], f"json failed: {r2}"
print("OK")
"""
        try:
            proc = subprocess.run(
                [sys.executable, "-c", test_script],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
                cwd=str(workdir / "multi_refactor"),
            )
            if proc.returncode == 0 and "OK" in proc.stdout:
                score += 0.25
        except Exception:
            pass

    return min(score, 1.0)
