content = open('darkclaude-app/src/App.tsx', encoding='utf-8-sig').read()

# 1. disabled={thinking} を削除
content = content.replace(
    'autoFocus disabled={thinking} spellCheck={false}',
    'autoFocus spellCheck={false}'
)

# 2. send() の先頭で thinking 中なら先に中断
content = content.replace(
    '  const send = async () => {\n',
    '  const send = async () => {\n    if (thinking) {\n      try { await fetch(`${API}/stop`, {method:"POST"}) } catch(e) {}\n      abortCtrl.current?.abort()\n      setThinking(false)\n      setThinkingTxt("")\n    }\n'
)

open('darkclaude-app/src/App.tsx', 'w', encoding='utf-8').write(content)
print("完了")
