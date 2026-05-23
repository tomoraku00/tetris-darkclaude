content = open('api/main.py', encoding='utf-8-sig').read()

content = content.replace(
    '_always_allow: set = set()',
    '_always_allow: set = set()\n_cancel_requested: bool = False'
)

content = content.replace(
    '@app.post("/chat")',
    '@app.post("/stop")\nasync def stop_generation():\n    global _cancel_requested\n    _cancel_requested = True\n    return {"status": "ok"}\n\n\n@app.post("/chat")'
)

content = content.replace(
    '        global _messages\n',
    '        global _messages, _cancel_requested\n        _cancel_requested = False\n'
)

cancel_check = '        while True:\n            if _cancel_requested:\n                _cancel_requested = False\n                yield "data: {\\"type\\":\\"text\\",\\"content\\":\\"[中断しました]\\"}\\n\\n"\n                yield "data: [DONE]\\n\\n"\n                return\n            sys_prompt = _inject_workdir'

content = content.replace(
    '        while True:\n            sys_prompt = _inject_workdir',
    cancel_check
)

open('api/main.py', 'w', encoding='utf-8').write(content)
print('完了')
