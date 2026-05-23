content = open('darkclaude-app/src/App.tsx', encoding='utf-8-sig').read()

keyboard_hook = """
  useEffect(() => {
    if (!approval) return
    const onKey = (e: KeyboardEvent) => {
      if (['1','2','3','Escape','Enter'].includes(e.key)) {
        e.preventDefault()
        e.stopPropagation()
        if (e.key === '1' || e.key === 'Enter') handleApproval('yes')
        else if (e.key === '2') handleApproval('always')
        else if (e.key === '3' || e.key === 'Escape') handleApproval('no')
      }
    }
    window.addEventListener('keydown', onKey, true)
    return () => window.removeEventListener('keydown', onKey, true)
  }, [approval])

"""

content = content.replace(
    '  const handleApproval = async (decision:string) => {',
    keyboard_hook + '  const handleApproval = async (decision:string) => {'
)

open('darkclaude-app/src/App.tsx', 'w', encoding='utf-8').write(content)
print("完了")
