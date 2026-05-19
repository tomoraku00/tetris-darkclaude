"""T07 セットアップ: deep_bug フィクスチャを workdir にコピー"""
import shutil
from pathlib import Path


def setup(workdir: Path, fixtures_dir: Path) -> None:
    src = fixtures_dir / "deep_bug"
    for f in src.iterdir():
        shutil.copy2(f, workdir / f.name)
