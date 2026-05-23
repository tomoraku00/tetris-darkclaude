import re
t = open('darkclaude-app/src/App.tsx', encoding='utf-8-sig').read()
i = t.index('const BANNER = `') + 16
banner = [''] + t[i:t.index('`', i)].splitlines()
i = t.index('const MASCOT = `') + 16
mascot = t[i:t.index('`', i)].splitlines()
css = open('darkclaude-app/src/App.css', encoding='utf-8-sig').read()
m = re.search(r'--banner:\s*(#[0-9a-fA-F]{6})', css)
hex_col = m.group(1) if m else '#2a2a2a'
r,g,b = int(hex_col[1:3],16),int(hex_col[3:5],16),int(hex_col[5:7],16)
m2 = re.search(r'--st-mode:\s*(#[0-9a-fA-F]{6})', css)
ph = m2.group(1) if m2 else '#b095d5'
pr,pg,pb = int(ph[1:3],16),int(ph[3:5],16),int(ph[5:7],16)
w = max(len(l) for l in banner) + 4
rows = max(len(banner), len(mascot))
out = ['$esc=[char]27', 'Clear-Host', 'Write-Host ""']
for i in range(rows):
    bl = banner[i] if i < len(banner) else ''
    ml = mascot[i] if i < len(mascot) else ''
    row = bl.ljust(w) + ml
    out.append('Write-Host "${esc}[38;2;' + str(r) + ';' + str(g) + ';' + str(b) + 'm' + row.replace("'","''") + '${esc}[0m"')
out.append('Write-Host ""')
out.append('$i=0')
out.append('while(!(Test-Path "$env:TEMP\\darkclaude_ready.tmp")){')
out.append('    $dots="."*(($i%3)+1)')
out.append('    Write-Host "`r  ${esc}[38;2;' + str(pr) + ';' + str(pg) + ';' + str(pb) + 'm起動中$dots${esc}[0m  " -NoNewline')
out.append('    $i++')
out.append('    Start-Sleep 1')
out.append('}')
open('splash.ps1', 'w', encoding='utf-16').write('\n'.join(out))
print('done: banner=' + hex_col + ' purple=' + ph)