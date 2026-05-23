content = open('darkclaude-app/src/App.css', encoding='utf-8-sig').read()
content = content.replace(
    '.chat-input{flex:1;background:transparent;',
    '.chat-input{resize:none;flex:1;background:transparent;'
)
open('darkclaude-app/src/App.css', 'w', encoding='utf-8').write(content)
print("完了")
