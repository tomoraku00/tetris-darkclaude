# DarkClaude ランチャー (TCP ポーリング版)

$llamaPath  = "C:\Users\tomo_rrow\Documents\nanoclaude"
$nanoPath   = "C:\Users\tomo_rrow\Documents\nanoclaude"
$serverPort = 8080
$maxWait    = 180

Write-Host "==> Starting llama-server in new window..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy", "Bypass",
    "-Command",
    "cd '$llamaPath'; .\start_llama_server.ps1"
)

Write-Host "==> Waiting for llama-server (TCP port $serverPort)..." -ForegroundColor Cyan
$elapsed = 0
$ready = $false
while ($elapsed -lt $maxWait) {
    Start-Sleep -Seconds 2
    $elapsed += 2
    try {
        $client = New-Object System.Net.Sockets.TcpClient
        $client.Connect("localhost", $serverPort)
        $client.Close()
        $ready = $true
        Write-Host "==> llama-server ready (${elapsed}s)" -ForegroundColor Green
        break
    } catch {
        if ($elapsed % 10 -eq 0) {
            Write-Host "  waiting... ${elapsed}s" -ForegroundColor DarkGray
        }
    }
}

if (-not $ready) {
    Write-Host "==> Timeout: llama-server did not respond within ${maxWait}s" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "==> Launching DarkClaude..." -ForegroundColor Cyan
Set-Location $nanoPath
python main.py
