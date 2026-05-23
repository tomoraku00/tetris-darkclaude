content = open('darkclaude-app/src/App.tsx', encoding='utf-8-sig').read()

stop_fn = """
  const handleStop = async () => {
    try { await fetch(`${API}/stop`, {method:"POST"}) } catch(e) {}
    abortCtrl.current?.abort()
    setThinking(false)
    setThinkingTxt("")
  }
"""

content = content.replace(
    '  const send = async () => {',
    stop_fn + '  const send = async () => {'
)

open('darkclaude-app/src/App.tsx', 'w', encoding='utf-8').write(content)
print("完了")
