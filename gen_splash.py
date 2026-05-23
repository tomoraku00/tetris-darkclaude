t=open('darkclaude-app/src/App.tsx',encoding='utf-8-sig').read()
i=t.index('const BANNER = `')+16; banner=t[i:t.index('`',i)]
i=t.index('const MASCOT = `')+16; mascot=t[i:t.index('`',i)]
out=[]
out.append('Clear-Host')
out.append('Write-Host ""')
for l in banner.splitlines():
    out.append("Write-Host '" + l.replace("'","''") + "' -ForegroundColor DarkGray")
out.append('Write-Host ""')
for l in mascot.splitlines():
    out.append("Write-Host '  " + l.replace("'","''") + "' -ForegroundColor DarkGray")
out.append('Write-Host ""')
out.append("$i=0")
out.append("while(!(Test-Path \"$env:TEMP\\darkclaude_ready.tmp\")){")
out.append("    $dots='.'*(($i%3)+1)")
out.append("    Write-Host \"`r  起動中$dots  \" -NoNewline -ForegroundColor Cyan")
out.append("    $i++")
out.append("    Start-Sleep 1")
out.append("}")
open('splash.ps1','w',encoding='utf-8').write('\n'.join(out))
print('done')