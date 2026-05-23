# DarkClaude ランチャー
$nanoPath  = "C:\Users\tomo_rrow\Documents\nanoclaude"
$llamaDir  = "$env:USERPROFILE\llamacpp\llama-b9264-bin-win-cuda-12.4-x64"
$modelPath = "$env:USERPROFILE\models\Qwen3.6-35B-A3B-UD-Q3_K_XL.gguf"

# スプラッシュ画面を表示
Remove-Item "$env:TEMP\darkclaude_ready.tmp" -Force -ErrorAction SilentlyContinue
$splash = Start-Process powershell -ArgumentList "-NoExit","-File","$nanoPath\splash.ps1" -PassThru

# 1. llama-server をバックグラウンドで起動
$cmd = "cd '$llamaDir'; .\llama-server.exe -m '$modelPath' -c 8192 -ngl 999 --n-cpu-moe 38 -fa on -t 16 -b 2048 -ub 2048 -ctk q4_0 -ctv q4_0 --port 8080 --jinja --reasoning off --reasoning-budget 0 --kv-unified"
$llamaProc = Start-Process powershell -WindowStyle Hidden -ArgumentList "-Command",$cmd -PassThru

# 2. llama-server が起動するまで待つ
$maxWait = 120; $elapsed = 0; $ready = $false
while ($elapsed -lt $maxWait) {
    try {
        $r = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:8080/health" -TimeoutSec 2 -ErrorAction Stop
        if ($r.StatusCode -eq 200) { $ready = $true; break }
    } catch {}
    Start-Sleep 2; $elapsed += 2
}

# 3. FastAPI をバックグラウンドで起動
$apiProc = Start-Process powershell -WindowStyle Hidden -ArgumentList "-Command","cd '$nanoPath'; python api/main.py" -PassThru
Start-Sleep 3

# 4. スプラッシュを閉じてTauriを起動
New-Item "$env:TEMP\darkclaude_ready.tmp" -Force | Out-Null
Start-Sleep 1
Stop-Process -Id $splash.Id -Force -ErrorAction SilentlyContinue
Remove-Item "$env:TEMP\darkclaude_ready.tmp" -Force -ErrorAction SilentlyContinue

Set-Location "$nanoPath\darkclaude-app"
npm run tauri dev

# 5. Tauri が閉じたらサーバーを停止
taskkill /F /T /PID $llamaProc.Id 2>$null
taskkill /F /T /PID $apiProc.Id 2>$null
Get-Process llama-server -ErrorAction SilentlyContinue | Stop-Process -Force
Write-Host "==> Done." -ForegroundColor Green
