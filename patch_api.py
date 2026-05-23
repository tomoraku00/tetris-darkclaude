path = r'C:/Users/tomo_rrow/Documents/nanoclaude/api/main.py'
with open(path,'r',encoding='utf-8') as f:
    c = f.read()
old1 = '            response = await asyncio.to_thread(client.chat, model, trimmed, TOOL_SCHEMAS)'
new1 = '            try:\n                response = await asyncio.wait_for(\n                    asyncio.to_thread(client.chat, model, trimmed, TOOL_SCHEMAS),\n                    timeout=120\n                )\n            except asyncio.TimeoutError:\n                import json as _j\n                yield "data: " + _j.dumps({"type":"error","content":"[timeout] No response in 120s."}) + "\n\n"\n                break'
old2 = '            tool_calls = msg.get("tool_calls") or []'
new2 = '            tool_calls = msg.get("tool_calls") or []\n            if not hasattr(generate, "_tool_hist"):\n                generate._tool_hist = []\n            if tool_calls:\n                sig = tool_calls[0].get("function",{}).get("name","") + str(tool_calls[0].get("function",{}).get("arguments",{}))[:80]\n                generate._tool_hist.append(sig)\n                if len(generate._tool_hist) >= 3 and len(set(generate._tool_hist[-3:])) == 1:\n                    _messages.append({"role":"tool","content":"[hint] Same op x3. Try different approach.","name":"system"})\n                    generate._tool_hist.clear()'
print("old1:", old1 in c)
print("old2:", old2 in c)
if old1 in c: c = c.replace(old1, new1)
if old2 in c: c = c.replace(old2, new2)
with open(path,"w",encoding="utf-8") as f: f.write(c)
print("Done")
