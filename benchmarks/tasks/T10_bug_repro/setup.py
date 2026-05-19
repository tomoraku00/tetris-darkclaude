"""T10 セットアップ: bug_repro フィクスチャを workdir にコピー"""
import shutil
from pathlib import Path


def setup(workdir: Path, fixtures_dir: Path) -> None:
    src = fixtures_dir / "bug_repro"
    for f in src.iterdir():
        shutil.copy2(f, workdir / f.name)
