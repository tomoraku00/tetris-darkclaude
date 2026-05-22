content = open('src/App.tsx', encoding='utf-8').read()
old = 'fetch(`${API}/messages`).then(r=>r.json()).then((data:any)=>{'
new = 'fetch(`${API}/messages`).then(r=>r.json()).then((data:any)=>{ if(!d.show_history){data={messages:[]}}; '
content = content.replace(old, new)
open('src/App.tsx', 'w', encoding='utf-8').write(content)
print('done')
