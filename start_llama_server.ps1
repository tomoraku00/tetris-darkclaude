# start_llama_server.ps1 - DarkClaude 用 llama-server 起動スクリプト
# 使い方: .\start_llama_server.ps1

$ErrorActionPreference = "Stop"

$llamaDir = "$env:USERPROFILE\llamacpp\llama-b9209-bin-win-cuda-12.4-x64"
$modelPath = "$env:USERPROFILE\models\Qwen3.6-35B-A3B-UD-Q4_K_M.gguf"

if (-not (Test-Path $llamaDir)) {
    Write-Error "llama.cpp directory not found: $llamaDir"
    exit 1
}
if (-not (Test-Path $modelPath)) {
    Write-Error "Model file not found: $modelPath"
    exit 1
}

Write-Host ""
Write-Host "Starting llama-server for DarkClaude..." -ForegroundColor Cyan
Write-Host "  Model:    $modelPath"
Write-Host "  Port:     8080"
Write-Host "  Context:  32768"
Write-Host "  Reasoning: off (budget=0)"
Write-Host ""

Push-Location $llamaDir
try {
    .\llama-server.exe `
      -m $modelPath `
      -c 32768 `
      -ngl 999 `
      --n-cpu-moe 32 `
      -fa on `
      -t 16 `
      -b 2048 -ub 2048 `
      -ctk q8_0 -ctv q8_0 `
      --port 8080 `
      --jinja `
      --reasoning off `
      --reasoning-budget 0
} finally {
    Pop-Location
}
