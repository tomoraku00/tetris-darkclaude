from pathlib import Path

PROJECT_ROOT = Path.cwd().resolve()


def resolve_path(path: str) -> Path:
    """パスをプロジェクトルート基準で絶対パスに解決する"""
    p = Path(path)
    if p.is_absolute():
        return p.resolve()
    return (PROJECT_ROOT / path).resolve()