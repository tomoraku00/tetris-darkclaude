"""T06 セットアップ: multi_refactor フィクスチャを workdir にコピー"""
import shutil
from pathlib import Path


def setup(workdir: Path, fixtures_dir: Path) -> None:
    src = fixtures_dir / "multi_refactor"
    dst = workdir / "multi_refactor"
    shutil.copytree(src, dst)
