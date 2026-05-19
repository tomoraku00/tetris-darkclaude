"""T03 セットアップ: refactor/ を workdir にコピー"""
import shutil
from pathlib import Path


def setup(workdir: Path, fixtures_dir: Path) -> None:
    src = fixtures_dir / "refactor"
    shutil.copytree(src, workdir, dirs_exist_ok=True)
