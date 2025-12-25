<#
.SYNOPSIS
    GitHub Issue Reporter Hook Script
.DESCRIPTION
    Claude Code Stopイベント時に自動的にGitHub Issueへ報告を促すスクリプト
    このスクリプトは通知のみを行い、実際の報告はClaude Codeが実行する
#>

param(
    [string]$Context = "Session Stop"
)

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$logFile = "C:\Users\Tenormusica\Documents\github-remote-desktop\logs\hook_execution.log"

# ログディレクトリ確認
$logDir = "C:\Users\Tenormusica\Documents\github-remote-desktop\logs"
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

# ログ記録
Add-Content -Path $logFile -Value "[$timestamp] GitHub Issue Reporter Hook triggered - Context: $Context"

# 通知音（オプション）
[console]::beep(800, 200)

Write-Host "GitHub Issue Reporter Hook executed at $timestamp"
