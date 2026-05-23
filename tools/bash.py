import re
import shutil
import subprocess
import time
from pathlib import Path

PROJECT_ROOT = Path.cwd().resolve()

_SHELL = shutil.which("pwsh") or shutil.which("powershell") or "powershell"

_MAX_OUTPUT = 4000

# PowerShell のコンソール出力を UTF-8 に強制するプリアンブル
# Windows のデフォルト cp932 出力のまま Python が utf-8 で読むと文字化けするため
_UTF8_PREAMBLE = (
    "$OutputEncoding = [System.Text.Encoding]::UTF8; "
    "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; "
)

# 壊滅的な破壊コマンドのみブロック（v0.6 で権限承認システムに置き換える）
_BLOCKED = [
    re.compile(r"Remove-Item.*-Recurse.*-Force\s+[A-Za-z]:\\", re.IGNORECASE),
    re.compile(r"Format-Volume", re.IGNORECASE),
    re.compile(r"Stop-Computer|Restart-Computer", re.IGNORECASE),
    re.compile(r"Clear-Disk", re.IGNORECASE),
]

SCHEMA = {
    "type": "function",
    "function": {
        "name": "bash",
        "description": "PowerShell コマンドを実行し stdout+stderr を返す。外部プロジェクトへのアクセス・ファイル一覧(Get-ChildItem)・インストール等に使う。他のツールで代替できる場合はそちらを優先。長時間処理は timeout を延長すること（デフォルト 120、最大 600）。",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "実行する PowerShell コマンド"
                },
                "timeout": {
                    "type": "integer",
                    "description": "実行時間上限（秒）。デフォルト 120、最大 600。長時間 I/O（ollama pull 等）の場合は明示的に指定すること",
                    "default": 120
                },
            },
            "required": ["command"]
        }
    }
}


def run(command: str, timeout: int = 120) -> str:
    for pattern in _BLOCKED:
        if pattern.search(command):
            return f"ERROR: blocked command: {pattern.pattern}"

    timeout = max(1, min(timeout, 600))

    try:
        proc = subprocess.run(
            [_SHELL, "-NonInteractive", "-Command", _UTF8_PREAMBLE + command],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            cwd=str(PROJECT_ROOT),
        )
    except subprocess.TimeoutExpired:
        return (
            f"ERROR: timeout after {timeout}s. "
            "If the command requires more time, retry with a larger timeout argument (max 600)."
        )
    except Exception as e:
        return f"ERROR: {e}"

    output = proc.stdout + proc.stderr
    if len(output) > _MAX_OUTPUT:
        output = output[:_MAX_OUTPUT] + "\n...[truncated]"

    if proc.returncode != 0:
        return f"ERROR: exit code {proc.returncode}\n{output}" if output else f"ERROR: exit code {proc.returncode}"

    return output if output.strip() else "(no output)"


def run_timed(command: str, timeout: int = 120) -> dict:
    for pattern in _BLOCKED:
        if pattern.search(command):
            return {"output": f"ERROR: blocked command: {pattern.pattern}", "elapsed_sec": 0}

    timeout = max(1, min(timeout, 600))

    start = time.time()
    try:
        proc = subprocess.run(
            [_SHELL, "-NonInteractive", "-Command", _UTF8_PREAMBLE + command],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            cwd=str(PROJECT_ROOT),
        )
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start
        return {
            "output": (
                f"ERROR: timeout after {timeout}s. "
                "If the command requires more time, retry with a larger timeout argument (max 600)."
            ),
            "elapsed_sec": round(elapsed, 3),
        }
    except Exception as e:
        elapsed = time.time() - start
        return {"output": f"ERROR: {e}", "elapsed_sec": round(elapsed, 3)}

    output = proc.stdout + proc.stderr
    if len(output) > _MAX_OUTPUT:
        output = output[:_MAX_OUTPUT] + "\n...[truncated]"

    elapsed = time.time() - start
    result_output = output if output.strip() else "(no output)"

    if proc.returncode != 0:
        result_output = f"ERROR: exit code {proc.returncode}\n{output}" if output else f"ERROR: exit code {proc.returncode}"

    return {"output": result_output, "elapsed_sec": round(elapsed, 3)}
