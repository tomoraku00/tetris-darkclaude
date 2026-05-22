# DarkClaude ランチャー
$nanoPath = "C:\Users\tomo_rrow\Documents\nanoclaude"

# 1. llama-server を別ウィンドウで起動
Write-Host "==> Starting llama-server..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-ExecutionPolicy","Bypass","-NoExit","-File","$nanoPath\start_llama_server.ps1" -WorkingDirectory $nanoPath

# 2. llama-server が起動するまで待つ
Write-Host "==> Waiting for llama-server..." -ForegroundColor Cyan
$maxWait = 120; $elapsed = 0; $ready = $false
while ($elapsed -lt $maxWait) {
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:8080/health" -TimeoutSec 2 -ErrorAction Stop
        if ($r.StatusCode -eq 200) { $ready = $true; break }
    } catch {}
    Start-Sleep 2; $elapsed += 2
    Write-Host "  waiting... ${elapsed}s" -ForegroundColor DarkGray
}
if (-not $ready) {
    Write-Host "==> Timeout" -ForegroundColor Red
    Read-Host "Press Enter to exit"; exit 1
}

# 3. FastAPI を別ウィンドウで起動
Write-Host "==> Starting FastAPI..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-ExecutionPolicy","Bypass","-NoExit","-Command","cd '$nanoPath'; python api/main.py" -WorkingDirectory $nanoPath
Start-Sleep 3

# 4. Tauri アプリを起動
Write-Host "==> Launching DarkClaude..." -ForegroundColor Cyan
Set-Location "$nanoPath\darkclaude-app"
npm run tauri dev
