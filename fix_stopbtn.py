content = open('darkclaude-app/src/App.tsx', encoding='utf-8-sig').read()

content = content.replace(
    '              autoFocus disabled={thinking} spellCheck={false} rows={1}/>\n          </div>',
    '              autoFocus disabled={thinking} spellCheck={false} rows={1}/>\n            {thinking && <button className="stop-btn" onClick={handleStop}>■</button>}\n          </div>'
)

open('darkclaude-app/src/App.tsx', 'w', encoding='utf-8').write(content)
print("完了")
