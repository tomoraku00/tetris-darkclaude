# DarkClaude ランチャー
$nanoPath  = "C:\Users\tomo_rrow\Documents\nanoclaude"
$llamaDir  = "$env:USERPROFILE\llamacpp\llama-b9264-bin-win-cuda-12.4-x64"
$modelPath = "$env:USERPROFILE\models\Qwen3.6-35B-A3B-UD-Q3_K_XL.gguf"
Remove-Item "$env:TEMP\darkclaude_ready.tmp" -Force -ErrorAction SilentlyContinue
$splash = Start-Process powershell -ArgumentList "-NoExit","-File","$nanoPath\splash.ps1" -PassThru
$cmd = "cd '$llamaDir'; .\llama-server.exe -m '$modelPath' -c 16384 -ngl 999 --n-cpu-moe 38 -fa on -t 16 -b 2048 -ub 2048 -ctk q8_0 -ctv q8_0 --port 8080 --jinja --reasoning off --reasoning-budget 0 --kv-unified"
$llamaProc = Start-Process powershell -WindowStyle Hidden -ArgumentList "-Command",$cmd -PassThru
$maxWait = 120; $elapsed = 0; $ready = $false
while ($elapsed -lt $maxWait) {
    try {
        $r = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:8080/health" -TimeoutSec 2 -ErrorAction Stop
        if ($r.StatusCode -eq 200) { $ready = $true; break }
    } catch {}
    Start-Sleep 2; $elapsed += 2
}
python "C:\Users\tomo_rrow\Documents\nanoclaude\fix_bom.py"
$apiProc = Start-Process powershell -WindowStyle Hidden -ArgumentList "-Command","cd 'C:\Users\tomo_rrow\Documents\nanoclaude'; python api/main.py" -PassThru
Start-Sleep 3
New-Item "$env:TEMP\darkclaude_ready.tmp" -Force | Out-Null
Start-Sleep 1
Stop-Process -Id $splash.Id -Force -ErrorAction SilentlyContinue
Remove-Item "$env:TEMP\darkclaude_ready.tmp" -Force -ErrorAction SilentlyContinue
Set-Location "C:\Users\tomo_rrow\Documents\nanoclaude\darkclaude-app"
npm run tauri dev
taskkill /F /T /PID $llamaProc.Id 2>$null
taskkill /F /T /PID $apiProc.Id 2>$null
Get-Process llama-server -ErrorAction SilentlyContinue | Stop-Process -Force
Write-Host "==> Done." -ForegroundColor Green