# -*- coding: utf-8 -*-
import os
from tools import bash, glob, read_file, str_replace, write_file

# grep は E16 で削除 (使用頻度 0、description 肥大化の要因)
_CODEGRAPH_AVAILABLE = os.path.exists(".codegraph/codegraph.db")

_TOOLS = {
    "read_file":         read_file.run,
    "write_file":        write_file.run,
    "bash":              bash.run,
    "glob":              glob.run,
    "str_replace":       str_replace.run,
}

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "ファイルを読み込む。",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string", "description": "ファイルパス"}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "str_replace",
            "description": "ファイルの文字列を置換する。old_str が一意に存在する必要がある。既存ファイル編集に使う（推奨）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "old_str": {"type": "string", "description": "置換対象（一意な文字列）"},
                    "new_str": {"type": "string", "description": "置換後"},
                },
                "required": ["path", "old_str", "new_str"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "新規ファイルを作成する。既存ファイル編集には str_replace を使うこと。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "glob",
            "description": "ファイルを検索する (例: '**/*.py', 'src/**/*.ts')。",
            "parameters": {
                "type": "object",
                "properties": {"pattern": {"type": "string"}},
                "required": ["pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": "シェルコマンドを実行する (Windows PowerShell)。&& は不可、; を使う。",
            "parameters": {
                "type": "object",
                "properties": {"command": {"type": "string"}},
                "required": ["command"],
            },
        },
    },
]

if _CODEGRAPH_AVAILABLE:
    from tools import codegraph_explore
    _TOOLS["codegraph_explore"] = codegraph_explore.run
    TOOL_SCHEMAS.append({
        "type": "function",
        "function": {
            "name": "codegraph_explore",
            "description": "コードベースのシンボル・関数・クラス・依存関係を検索する。grep/glob/read_file より高速で効率的。",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "検索クエリ (例: 'dispatch tool_call', 'chat_turn loop')"}},
                "required": ["query"],
            },
        },
    })

_PLAN_BLOCKED = {"write_file", "bash"}

def dispatch(name: str, args: dict, plan_mode: bool = False) -> str:
    if plan_mode and name in _PLAN_BLOCKED:
        return (
            f"ERROR: {name} は Plan モード中は使用できません。"
            "/plan で通常モードに戻してください。"
        )
    if name not in _TOOLS:
        return f"ERROR: unknown tool '{name}'"
    try:
        return _TOOLS[name](**args)
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {e}"
