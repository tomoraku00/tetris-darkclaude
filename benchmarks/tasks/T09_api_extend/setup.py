"""T09 セットアップ: api_extend フィクスチャを workdir にコピー"""
import shutil
from pathlib import Path


def setup(workdir: Path, fixtures_dir: Path) -> None:
    src = fixtures_dir / "api_extend"
    shutil.copytree(src, workdir / "api_extend")
    # DARKCLAUDE.md を workdir ルートにも配置 (DarkClaude の CWD = workdir のため)
    dmd = src / "DARKCLAUDE.md"
    if dmd.exists():
        shutil.copy(dmd, workdir / "DARKCLAUDE.md")
