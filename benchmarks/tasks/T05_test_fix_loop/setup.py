"""T05 セットアップ: test_loop/ を workdir にコピー"""
import shutil
from pathlib import Path


def setup(workdir: Path, fixtures_dir: Path) -> None:
    src = fixtures_dir / "test_loop"
    shutil.copytree(src, workdir, dirs_exist_ok=True)
