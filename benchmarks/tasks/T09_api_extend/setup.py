"""T09 セットアップ: api_extend フィクスチャを workdir にコピー"""
import shutil
from pathlib import Path


def setup(workdir: Path, fixtures_dir: Path) -> None:
    src = fixtures_dir / "api_extend"
    shutil.copytree(src, workdir / "api_extend")
