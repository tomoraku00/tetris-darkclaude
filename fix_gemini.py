import re

content = open("api/main.py", encoding="utf-8").read()

# 1. get_fallback_client 関数を get_client の直後に追加
fallback_func = '''
def get_fallback_client():
    """Gemini等のフォールバッククライアントを返す"""
    from clients.openai_client import OpenAIClient
    cfg = load_config()
    base_url = cfg.get("fallback_base_url", "")
    api_key = cfg.get("fallback_api_key", "")
    if not base_url or not api_key:
        return None
    return OpenAIClient(base_url=base_url, api_key=api_key)

'''

if "get_fallback_client" not in content:
    content = content.replace("def _inject_workdir", fallback_func + "def _inject_workdir")

# 2. raw JSON 検出時にフォールバック切替を追加
old = """            if not tool_calls:
                content_text = msg.get("content", "")
                raw_calls, clean_text = _extract_raw_tool_calls(content_text)
                if raw_calls:
                    tool_calls = raw_calls
                    if clean_text and clean_text.strip():
                        yield f"data: {json.dumps({'type':'text','content':clean_text})}\\n\\n"
                else:
                    yield f"data: {json.dumps({'type':'text','content':content_text})}\\n\\n"
                    break"""

new = """            if not tool_calls:
                content_text = msg.get("content", "")
                raw_calls, clean_text = _extract_raw_tool_calls(content_text)
                if raw_calls and _config.get("fallback_enabled") and not used_fallback:
                    used_fallback = True
                    client = get_fallback_client()
                    model = _config.get("fallback_model", "gemini-2.0-flash")
                    yield f"data: {json.dumps({'type':'text','content':'[Gemini にフォールバック中...]'})}\\n\\n"
                    if client is None:
                        tool_calls = raw_calls
                    else:
                        continue
                elif raw_calls:
                    tool_calls = raw_calls
                    if clean_text and clean_text.strip():
                        yield f"data: {json.dumps({'type':'text','content':clean_text})}\\n\\n"
                else:
                    yield f"data: {json.dumps({'type':'text','content':content_text})}\\n\\n"
                    break"""

content = content.replace(old, new)

# 3. used_fallback フラグを while ループの前に追加
content = content.replace(
    "        while True:\n",
    "        used_fallback = False\n        while True:\n"
)

open("api/main.py", "w", encoding="utf-8").write(content)
print("done")
