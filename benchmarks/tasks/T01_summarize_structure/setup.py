"""T01 セットアップ: small_project を workdir にコピー"""
import shutil
from pathlib import Path


def setup(workdir: Path, fixtures_dir: Path) -> None:
    src = fixtures_dir / "small_project"
    shutil.copytree(src, workdir, dirs_exist_ok=True)
