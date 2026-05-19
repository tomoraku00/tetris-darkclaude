"""T13 セットアップ: type_chain フィクスチャを workdir にコピー"""
import shutil
from pathlib import Path


def setup(workdir: Path, fixtures_dir: Path) -> None:
    src = fixtures_dir / "type_chain"
    for item in src.iterdir():
        shutil.copy2(item, workdir / item.name)
