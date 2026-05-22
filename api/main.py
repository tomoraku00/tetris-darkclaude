import re
# -*- coding: utf-8 -*-
"""DarkClaude FastAPI backend - Skills / Resumable / Approval"""
import sys, json, asyncio, uuid, sqlite3
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

app = FastAPI(title="DarkClaude API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_CONFIG_PATH = Path(__file__).parent.parent / "config.json"
_DB_PATH = Path(__file__).parent.parent / ".darkclaude" / "sessions.db"
_SKILLS_DIR = Path(__file__).parent.parent / ".darkclaude" / "skills"

APPROVAL_TOOLS = {"write_file", "bash", "str_replace"}

_config = {}
_messages = []
_client = None
_current_session_id = None
plan_mode = False
_pending_approvals = {}
_approval_decisions = {}
_always_allow = set()


def _load_config():
    try:
        return json.loads(_CONFIG_PATH.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}



import re

def _inject_workdir(messages, system_prompt):
    for m in reversed(messages):
        if m.get("role") == "user":
            text = str(m.get("content", ""))
            match = re.search(r"作業ディレクトリ[：:]\s*([^\s\n]+)", text)
            if match:
                workdir = match.group(1).replace("\\", "/")
                return system_prompt + f"\n\n現在の作業ディレクトリ: {workdir}\n相対パスは {workdir}/相対パス の形式で read_file を呼ぶこと。"
    return system_prompt

def _trim_messages(messages, max_chars=20000):
    """コンテキストが長すぎる場合、古いメッセージを削除する"""
    total = sum(len(str(m.get("content","")))+len(str(m.get("tool_calls",""))) for m in messages)
    if total <= max_chars:
        return messages
    # system prompt は保持、古いメッセージから削除
    system = [m for m in messages if m.get("role") == "system"]
    others = [m for m in messages if m.get("role") != "system"]
    while len(others) > 4 and total > max_chars:
        removed = others.pop(0)
        total -= len(str(removed.get("content","")))
    return system + others

def get_client():
    global _client
    if _client is None:
        from clients import get_client as _gc
        _client = _gc(_config)
    return _client


# ---- SQLite sessions ----

def init_db():
    _DB_PATH.parent.mkdir(exist_ok=True)
    con = sqlite3.connect(_DB_PATH)
    con.execute("""CREATE TABLE IF NOT EXISTS sessions
        (id TEXT PRIMARY KEY, created_at TEXT, updated_at TEXT)""")
    con.execute("""CREATE TABLE IF NOT EXISTS messages
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
         session_id TEXT, role TEXT, content TEXT,
         tool_calls TEXT, name TEXT, created_at TEXT)""")
    con.commit(); con.close()


def _new_session():
    sid = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    con = sqlite3.connect(_DB_PATH)
    con.execute("INSERT INTO sessions VALUES (?,?,?)", (sid, now, now))
    con.commit(); con.close()
    return sid


def _save_msg(session_id, msg):
    con = sqlite3.connect(_DB_PATH)
    con.execute(
        "INSERT INTO messages(session_id,role,content,tool_calls,name,created_at) VALUES(?,?,?,?,?,?)",
        (session_id, msg.get("role",""), msg.get("content") or "",
         json.dumps(msg["tool_calls"]) if msg.get("tool_calls") else None,
         msg.get("name"), datetime.utcnow().isoformat()))
    con.execute("UPDATE sessions SET updated_at=? WHERE id=?",
                (datetime.utcnow().isoformat(), session_id))
    con.commit(); con.close()


def _load_latest():
    con = sqlite3.connect(_DB_PATH)
    row = con.execute("SELECT id FROM sessions ORDER BY updated_at DESC LIMIT 1").fetchone()
    if not row:
        con.close(); return None, []
    sid = row[0]
    rows = con.execute(
        "SELECT role,content,tool_calls,name FROM messages WHERE session_id=? ORDER BY id",
        (sid,)).fetchall()
    con.close()
    msgs = []
    for role, content, tc_json, name in rows:
        m = {"role": role, "content": content}
        if tc_json: m["tool_calls"] = json.loads(tc_json)
        if name: m["name"] = name
        msgs.append(m)
    return sid, msgs


# ---- Skills ----

def _skills_context(user_message):
    try:
        from tools.skills import load_skills, select_relevant_skills, build_skill_context
        skills = load_skills(_SKILLS_DIR)
        relevant = select_relevant_skills(skills, user_message)
        return build_skill_context(relevant)
    except Exception:
        return ""


# ---- System prompt ----

def _get_system_prompt(skills_ctx=""):
    from prompts import SYSTEM_PROMPT
    if skills_ctx:
        return SYSTEM_PROMPT + "\n\n# 関連スキル\n" + skills_ctx
    return SYSTEM_PROMPT


def reset_messages(new_session=True):
    global _messages, _current_session_id
    if new_session:
        _current_session_id = _new_session()
    sys_msg = {"role": "system", "content": _get_system_prompt()}
    _messages = [sys_msg]
    _save_msg(_current_session_id, sys_msg)


# ---- Startup ----

@app.on_event("startup")
async def startup():
    global _config, _messages, _current_session_id
    _config.update(_load_config())
    init_db()
    from prompts import SYSTEM_PROMPT
    sid, msgs = _load_latest()
    if sid and msgs:
        _current_session_id = sid
        _messages = msgs
        if not _messages or _messages[0].get("role") != "system":
            _messages.insert(0, {"role": "system", "content": SYSTEM_PROMPT})
    else:
        reset_messages()


# ---- Models ----

class ChatRequest(BaseModel):
    message: str

class ApproveRequest(BaseModel):
    id: str
    decision: str  # allow | allow_always | deny


# ---- Endpoints ----

@app.get("/health")
def health():
    return {"status": "ok", "model": _config.get("model", "unknown")}


@app.get("/status")
def status():
    try:
        import subprocess
        r = subprocess.run(
            ["nvidia-smi","--query-gpu=memory.used,memory.free","--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=3)
        parts = r.stdout.strip().split(", ")
        vu, vf = int(parts[0]), int(parts[1])
    except Exception:
        vu, vf = 0, 0
    return {"model": _config.get("model","unknown"),
            "base_url": _config.get("base_url","http://localhost:8080"),
            "vram_used": vu, "vram_free": vf,
            "session_id": _current_session_id, "show_history": _config.get("show_history_on_startup", True)}


@app.post("/approve")
async def approve(req: ApproveRequest):
    if req.decision == "allow_always":
        # tool name を approval ID から取得するために decisions に保存
        pass
    if req.id in _pending_approvals:
        _approval_decisions[req.id] = req.decision
        _pending_approvals[req.id].set()
    return {"status": "ok"}


@app.get("/sessions")
def list_sessions():
    con = sqlite3.connect(_DB_PATH)
    rows = con.execute(
        "SELECT id,created_at,updated_at FROM sessions ORDER BY updated_at DESC LIMIT 20"
    ).fetchall()
    con.close()
    return {"sessions": [{"id":r[0],"created_at":r[1],"updated_at":r[2]} for r in rows],
            "current": _current_session_id}


@app.post("/chat")
async def chat(req: ChatRequest):
    from tools.registry import TOOL_SCHEMAS, dispatch

    async def generate():
        global _messages

        # Skills injection
        skills_ctx = _skills_context(req.message)
        if skills_ctx and _messages and _messages[0]["role"] == "system":
            _messages[0] = {"role":"system","content": _get_system_prompt(skills_ctx)}

        user_msg = {"role": "user", "content": req.message}
        _messages.append(user_msg)
        _save_msg(_current_session_id, user_msg)

        client = get_client()
        model = _config.get("model", "default")

        while True:
            sys_prompt = _inject_workdir(_messages, _get_system_prompt())
            if plan_mode:
                sys_prompt += "\n\n## Plan Mode\nツールを一切使わず、実行計画のみを日本語で番号付きリストで出力すること。最後に '計画を確認しました。/go で実行します。' と書くこと。"
            trimmed = _trim_messages(_messages)
            trimmed = [m for m in trimmed if m.get("role") != "system"]
            trimmed = [{"role": "system", "content": sys_prompt}] + trimmed
            response = await asyncio.to_thread(client.chat, model, trimmed, TOOL_SCHEMAS)
            msg = response.get("message", {})
            _messages.append(msg)
            _save_msg(_current_session_id, msg)

            tool_calls = msg.get("tool_calls") or []
            if not tool_calls:
                yield f"data: {json.dumps({'type':'text','content':msg.get('content','')})}\n\n"
                break

            for tc in tool_calls:
                name = tc.get("function",{}).get("name","")
                args = tc.get("function",{}).get("arguments",{})
                yield f"data: {json.dumps({'type':'tool_call','name':name,'args':args})}\n\n"

                # 承認チェック
                if name in APPROVAL_TOOLS and name not in _always_allow:
                    aid = str(uuid.uuid4())
                    ev = asyncio.Event()
                    _pending_approvals[aid] = ev
                    args_str = json.dumps(args, ensure_ascii=False, indent=2) if isinstance(args, dict) else str(args)
                    approval_event = {
                        'type': 'approval_needed',
                        'id': aid,
                        'title': f'\u23fa {name}(...)',
                        'command': args_str,
                        'emphasis': name,
                        'name': name,
                        'args': args,
                    }
                    yield f"data: {json.dumps(approval_event)}\n\n"
                    try:
                        await asyncio.wait_for(ev.wait(), timeout=120)
                    except asyncio.TimeoutError:
                        del _pending_approvals[aid]
                        result = "USER_DENIED: timeout"
                        tool_msg = {"role":"tool","content":result,"name":name}
                        _messages.append(tool_msg); _save_msg(_current_session_id, tool_msg)
                        yield f"data: {json.dumps({'type':'tool_result','name':name,'result':result})}\n\n"
                        continue

                    decision = _approval_decisions.pop(aid, "deny")
                    del _pending_approvals[aid]

                    if decision == "allow_always":
                        _always_allow.add(name)
                    elif decision == "deny":
                        result = "USER_DENIED: ユーザーが操作を拒否しました"
                        tool_msg = {"role":"tool","content":result,"name":name}
                        _messages.append(tool_msg); _save_msg(_current_session_id, tool_msg)
                        yield f"data: {json.dumps({'type':'tool_result','name':name,'result':result})}\n\n"
                        continue

                result = await asyncio.to_thread(dispatch, name, args)
                tool_msg = {"role":"tool","content":result,"name":name}
                _messages.append(tool_msg); _save_msg(_current_session_id, tool_msg)
                yield f"data: {json.dumps({'type':'tool_result','name':name,'result':result})}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")



@app.get("/messages")
def get_messages():
    """表示用メッセージ一覧（system除く）"""
    display = []
    for m in _messages:
        if m.get("role") == "system":
            continue
        display.append({
            "role": m.get("role"),
            "content": m.get("content") or "",
            "name": m.get("name"),
            "has_tool_calls": bool(m.get("tool_calls")),
        })
    return {"messages": display, "session_id": _current_session_id, "show_history": _config.get("show_history_on_startup", True)}


@app.post("/plan_mode")
async def set_plan_mode(body: dict):
    global plan_mode
    plan_mode = body.get("mode", False)
    return {"plan_mode": plan_mode}

@app.post("/clear")
def clear():
    reset_messages()
    return {"status": "ok", "session_id": _current_session_id, "show_history": _config.get("show_history_on_startup", True)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8765)