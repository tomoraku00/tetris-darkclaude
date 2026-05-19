"""T04 セットアップ: multi_file/ を workdir にコピー"""
import shutil
from pathlib import Path


def setup(workdir: Path, fixtures_dir: Path) -> None:
    src = fixtures_dir / "multi_file"
    shutil.copytree(src, workdir, dirs_exist_ok=True)
