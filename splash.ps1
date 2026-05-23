# 起動中スプラッシュ画面
$Host.UI.RawUI.WindowTitle = "DarkClaude - 起動中..."
Clear-Host
Write-Host ""
Write-Host " ██████╗  █████╗ ██████╗ ██╗  ██╗" -ForegroundColor DarkGray
Write-Host " ██╔══██╗██╔══██╗██╔══██╗██║ ██╔╝" -ForegroundColor DarkGray
Write-Host " ██║  ██║███████║██████╔╝█████╔╝ " -ForegroundColor DarkGray
Write-Host " ██║  ██║██╔══██║██╔══██╗██╔═██╗ " -ForegroundColor DarkGray
Write-Host " ██████╔╝██║  ██║██║  ██║██║  ██╗" -ForegroundColor DarkGray
Write-Host " ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝" -ForegroundColor DarkGray
Write-Host ""
Write-Host "        ▓▓  ▓" -ForegroundColor DarkGray
Write-Host "       ████▓██" -ForegroundColor DarkGray
Write-Host "      ████████" -ForegroundColor DarkGray
Write-Host "       ██████ " -ForegroundColor DarkGray
Write-Host ""

$i = 0
while (!(Test-Path "$env:TEMP\darkclaude_ready.tmp")) {
    $dots = "." * (($i % 3) + 1)
    Write-Host "`r  起動中$dots   " -NoNewline -ForegroundColor Cyan
    $i++
    Start-Sleep 1
}
