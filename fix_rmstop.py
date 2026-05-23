content = open('darkclaude-app/src/App.tsx', encoding='utf-8-sig').read()
content = content.replace(
    '\n            {thinking && <button className="stop-btn" onClick={handleStop}>■</button>}',
    ''
)
open('darkclaude-app/src/App.tsx', 'w', encoding='utf-8').write(content)
print("完了")
