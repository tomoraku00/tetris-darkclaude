"""T11 セットアップ: large_rename フィクスチャを workdir にコピー"""
import shutil
from pathlib import Path


def setup(workdir: Path, fixtures_dir: Path) -> None:
    src = fixtures_dir / "large_rename"
    for item in src.iterdir():
        dst = workdir / item.name
        if item.is_dir():
            shutil.copytree(item, dst)
        else:
            shutil.copy2(item, dst)
