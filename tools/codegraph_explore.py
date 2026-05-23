# -*- coding: utf-8 -*-
"""CodeGraph 経由でコードベースを検索するツール。"""
import subprocess
from pathlib import Path


def run(query: str, project_path: str = "") -> str:
    """CodeGraph でシンボル・ファイル・関係を検索する。
    grep/glob/read_file の代替として使用できる。
    """
    cwd = project_path if project_path else str(Path.cwd())
    try:
        result = subprocess.run(
            ["codegraph.cmd", "context", query],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            cwd=cwd,
        )
        if result.returncode != 0:
            # context が失敗したら query にフォールバック
            result = subprocess.run(
                ["codegraph.cmd", "query", query],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
                cwd=cwd,
            )
        output = result.stdout.strip()
        if not output:
            return "No results found."
        return output[:8000]  # 長すぎる場合は切る
    except subprocess.TimeoutExpired:
        return "ERROR: codegraph timeout (30s)"
    except FileNotFoundError:
        return "ERROR: codegraph not found. Run: npm install -g @colbymchenry/codegraph"
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {e}"
