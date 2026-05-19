"""T12 セットアップ: race_condition フィクスチャを workdir にコピー"""
import shutil
from pathlib import Path


def setup(workdir: Path, fixtures_dir: Path) -> None:
    src = fixtures_dir / "race_condition"
    for item in src.iterdir():
        shutil.copy2(item, workdir / item.name)
