import re

content = open("api/main.py", encoding="utf-8").read()

extract_func = '''
def _extract_raw_tool_calls(text):
    """テキスト中の生JSONツール呼び出しを抽出"""
    if not text or not text.strip().startswith("{"):
        return None, text
    try:
        data = json.loads(text.strip())
        if "tool_calls" in data:
            return data["tool_calls"], data.get("text", "")
    except Exception:
        pass
    return None, text

'''

if "_extract_raw_tool_calls" not in content:
    content = content.replace("def _inject_workdir", extract_func + "def _inject_workdir")

old = """            tool_calls = msg.get("tool_calls") or []
            if not tool_calls:
                yield f"data: {json.dumps({'type':'text','content':msg.get('content','')})}\n\n"
                break"""

new = """            tool_calls = msg.get("tool_calls") or []
            if not tool_calls:
                content_text = msg.get("content", "")
                raw_calls, clean_text = _extract_raw_tool_calls(content_text)
                if raw_calls:
                    tool_calls = raw_calls
                    if clean_text and clean_text.strip():
                        yield f"data: {json.dumps({'type':'text','content':clean_text})}\\n\\n"
                else:
                    yield f"data: {json.dumps({'type':'text','content':content_text})}\\n\\n"
                    break"""

content = content.replace(old, new)
open("api/main.py", "w", encoding="utf-8").write(content)
print("done")
