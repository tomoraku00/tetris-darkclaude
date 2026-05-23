content = open('darkclaude-app/src/App.css', encoding='utf-8-sig').read()
content = content.replace(
    '.approval-cmd{background:var(--code-bg);color:var(--output);padding:6px 8px 6px 16px;white-space:pre-wrap;margin:2px 0}',
    '.approval-cmd{background:var(--code-bg);color:var(--output);padding:6px 8px 6px 16px;white-space:pre-wrap;margin:2px 0;max-height:200px;overflow-y:auto}'
)
open('darkclaude-app/src/App.css', 'w', encoding='utf-8').write(content)
print("完了")
