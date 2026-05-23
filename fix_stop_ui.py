content = open('darkclaude-app/src/App.tsx', encoding='utf-8-sig').read()

# 1. AbortController ref 追加（既存の ref の近くに）
content = content.replace(
    'const [approval,setApproval] = useState<ApprovalData|null>(null)',
    'const [approval,setApproval] = useState<ApprovalData|null>(null)\n  const abortCtrl = useRef<AbortController|null>(null)'
)

# 2. fetch に signal を追加
content = content.replace(
    'const res=await fetch(`${API}/chat`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message:text})})',
    'abortCtrl.current = new AbortController()\n      const res=await fetch(`${API}/chat`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message:text}),signal:abortCtrl.current.signal})'
)

# 3. handleStop 関数追加（handleSend の近くに）
stop_fn = '''
  const handleStop = async () => {
    try { await fetch(`${API}/stop`, {method:"POST"}) } catch {}
    abortCtrl.current?.abort()
    setThinking(false)
    setThinkingTxt("")
  }
'''
content = content.replace(
    'const handleStop',
    '// already exists'
)
if 'handleStop' not in content:
    content = content.replace(
        '  const handleSend',
        stop_fn + '  const handleSend'
    )

open('darkclaude-app/src/App.tsx', 'w', encoding='utf-8').write(content)
print("App.tsx 完了")
