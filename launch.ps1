# DarkClaude ランチャー
# llama-server を別ウィンドウで起動 → ヘルスチェック → DarkClaude をこのウィンドウで起動

$llamaPath = "$env:USERPROFILE\llamacpp"   # ← 実際の llamacpp ディレクトリパスに変更
$nanoPath  = "C:\Users\tomo_rrow\Documents\nanoclaude"
$healthUrl = "http://localhost:8080/health"
$maxWait   = 120  # 秒

Write-Host "==> Starting llama-server in new window..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$llamaPath'; .\start_llama_server.ps1"
)

Write-Host "==> Waiting for llama-server to become ready..." -ForegroundColor Cyan
$elapsed = 0
$ready = $false
while ($elapsed -lt $maxWait) {
    Start-Sleep -Seconds 2
    $elapsed += 2
    try {
        $r = Invoke-WebRequest -Uri $healthUrl -UseBasicParsing -TimeoutSec 1 -ErrorAction Stop
        if ($r.StatusCode -eq 200) {
            $ready = $true
            Write-Host "==> llama-server ready (${elapsed}s)" -ForegroundColor Green
            break
        }
    } catch {
        Write-Host "  waiting... ${elapsed}s" -ForegroundColor DarkGray
    }
}

if (-not $ready) {
    Write-Host "==> Timeout: llama-server did not respond within ${maxWait}s" -ForegroundColor Red
    Write-Host "    Check the llama-server window for errors." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "==> Launching DarkClaude..." -ForegroundColor Cyan
Set-Location $nanoPath
python main.py
