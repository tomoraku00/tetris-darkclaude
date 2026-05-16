import re
import shutil
import subprocess
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
        "description": "PowerShell コマンドをプロジェクトルートで実行し、stdout+stderr を返す。",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "実行する PowerShell コマンド"
                }
            },
            "required": ["command"]
        }
    }
}


def run(command: str) -> str:
    for pattern in _BLOCKED:
        if pattern.search(command):
            return f"ERROR: blocked command: {pattern.pattern}"

    try:
        proc = subprocess.run(
            [_SHELL, "-NonInteractive", "-Command", _UTF8_PREAMBLE + command],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            cwd=str(PROJECT_ROOT),
        )
    except subprocess.TimeoutExpired:
        return "ERROR: timeout after 30s"
    except Exception as e:
        return f"ERROR: {e}"

    output = proc.stdout + proc.stderr
    if len(output) > _MAX_OUTPUT:
        output = output[:_MAX_OUTPUT] + "\n...[truncated]"

    if proc.returncode != 0:
        return f"ERROR: exit code {proc.returncode}\n{output}" if output else f"ERROR: exit code {proc.returncode}"

    return output if output.strip() else "(no output)"
