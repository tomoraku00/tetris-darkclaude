content = open('api/main.py', encoding='utf-8').read()
old = '"session_id": _current_session_id}'
new = '"session_id": _current_session_id, "show_history": _config.get("show_history_on_startup", True)}'
content = content.replace(old, new)
open('api/main.py', 'w', encoding='utf-8').write(content)
print('done')
