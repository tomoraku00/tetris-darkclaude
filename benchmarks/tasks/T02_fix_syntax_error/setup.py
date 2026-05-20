"""T02 セットアップ: bug.py を workdir にコピー"""
import shutil
from pathlib import Path


def setup(workdir: Path, fixtures_dir: Path) -> None:
    fixture_dir = fixtures_dir / "bug_files" / "syntax_error"
    shutil.copy(fixture_dir / "bug.py", workdir / "bug.py")
    dmd = fixture_dir / "DARKCLAUDE.md"
    if dmd.exists():
        shutil.copy(dmd, workdir / "DARKCLAUDE.md")
