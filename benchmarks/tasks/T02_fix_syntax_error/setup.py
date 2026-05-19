"""T02 セットアップ: bug.py を workdir にコピー"""
import shutil
from pathlib import Path


def setup(workdir: Path, fixtures_dir: Path) -> None:
    src = fixtures_dir / "bug_files" / "syntax_error" / "bug.py"
    shutil.copy(src, workdir / "bug.py")
