"""T08 セットアップ: perf_task フィクスチャを workdir にコピー"""
import shutil
from pathlib import Path


def setup(workdir: Path, fixtures_dir: Path) -> None:
    src = fixtures_dir / "perf_task"
    for f in src.iterdir():
        shutil.copy2(f, workdir / f.name)
