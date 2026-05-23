content = open('darkclaude-app/src/App.css', encoding='utf-8-sig').read()
content = content.replace(
    '.chat-input {',
    '.chat-input {\n  resize: none;'
)
open('darkclaude-app/src/App.css', 'w', encoding='utf-8').write(content)
print("完了")
