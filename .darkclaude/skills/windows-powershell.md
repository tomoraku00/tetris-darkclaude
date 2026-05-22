---
name: windows-powershell
description: Windows PowerShell コマンド集
keywords: [powershell, windows, shell, bat, ps1, コマンド]
---
## Windows PowerShell 注意事項

- && は使えない → ; を使う
- 環境変数: $env:USERPROFILE
- 文字コード: $env:PYTHONIOENCODING = utf-8
- ファイル書き込み: Out-File -Encoding UTF8
