# -*- coding: utf-8 -*-
"""DarkClaude FastAPI バックエンド"""
import sys, json, asyncio
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

app = FastAPI(title="DarkClaude API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_CONFIG_PATH = Path(__file__).parent.parent / "config.json"

def _load_config():
    try:
        return json.loads(_CONFIG_PATH.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}

# グローバル状態
_config = _load_config()
_messages = []
_client = None

def get_client():
    global _client
    if _client is None:
        from clients import get_client as _get_client
        _client = _get_client(_config)
    return _client

def reset_messages():
    global _messages
    from prompts import SYSTEM_PROMPT
    _messages = [{"role": "system", "content": SYSTEM_PROMPT}]

reset_messages()


class ChatRequest(BaseModel):
    message: str


@app.get("/health")
def health():
    return {"status": "ok", "model": _config.get("model", "unknown")}


@app.get("/status")
def status():
    try:
        import subprocess
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used,memory.free", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=3
        )
        if result.returncode == 0:
            parts = result.stdout.strip().split(", ")
            vram_used = int(parts[0])
            vram_free = int(parts[1])
        else:
            vram_used, vram_free = 0, 0
    except Exception:
        vram_used, vram_free = 0, 0
    return {
        "model": _config.get("model", "unknown"),
        "base_url": _config.get("base_url", "http://localhost:8080"),
        "vram_used": vram_used,
        "vram_free": vram_free,
    }


@app.post("/chat")
async def chat(req: ChatRequest):
    from tools.registry import TOOL_SCHEMAS, dispatch

    async def generate():
        global _messages
        _messages.append({"role": "user", "content": req.message})
        client = get_client()
        model = _config.get("model", "default")

        while True:
            response = await asyncio.to_thread(
                client.chat, model, _messages, TOOL_SCHEMAS
            )
            msg = response.get("message", {})
            _messages.append(msg)
            tool_calls = msg.get("tool_calls") or []

            if not tool_calls:
                content = msg.get("content", "")
                yield f"data: {json.dumps({'type': 'text', 'content': content})}\n\n"
                break

            for tc in tool_calls:
                name = tc.get("function", {}).get("name", "")
                args = tc.get("function", {}).get("arguments", {})
                yield f"data: {json.dumps({'type': 'tool_call', 'name': name, 'args': args})}\n\n"
                result = await asyncio.to_thread(dispatch, name, args)
                _messages.append({"role": "tool", "content": result, "name": name})
                yield f"data: {json.dumps({'type': 'tool_result', 'name': name, 'result': result[:500]})}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.post("/clear")
def clear():
    reset_messages()
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8765)
