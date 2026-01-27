<#
.SYNOPSIS
    GitHub Issue Reporter Hook Script v2
.DESCRIPTION
    Claude Code Stopイベント時に自動的にGitHub Issueへ報告を実行
    一時ファイルから回答内容を読み取り、task_complete_private.pyで報告
#>

param(
    [string]$Context = "Session Stop"
)

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$logDir = "C:\Users\Tenormusica\Documents\github-remote-desktop\logs"
$logFile = "$logDir\hook_execution.log"
$pendingReportFile = "C:\Users\Tenormusica\Documents\github-remote-desktop\pending_report.txt"
$pythonScript = "C:\Users\Tenormusica\Documents\github-remote-desktop\task_complete_private.py"

# Ensure log directory exists
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

# Log execution
Add-Content -Path $logFile -Value "[$timestamp] GitHub Issue Reporter v2 triggered - Context: $Context"

try {
    # Check if pending report file exists
    if (Test-Path $pendingReportFile) {
        # Read the pending report content
        $reportContent = Get-Content -Path $pendingReportFile -Raw -Encoding UTF8

        if ($reportContent -and $reportContent.Trim().Length -gt 0) {
            Add-Content -Path $logFile -Value "[$timestamp] Found pending report, executing..."

            # Execute the Python script with the report content
            $process = Start-Process -FilePath "python" `
                -ArgumentList "`"$pythonScript`" `"$reportContent`"" `
                -NoNewWindow -Wait -PassThru

            Add-Content -Path $logFile -Value "[$timestamp] Python script exit code: $($process.ExitCode)"

            # Delete the pending report file after successful execution
            if ($process.ExitCode -eq 0) {
                Remove-Item -Path $pendingReportFile -Force
                Add-Content -Path $logFile -Value "[$timestamp] Pending report file deleted"
            }
        } else {
            Add-Content -Path $logFile -Value "[$timestamp] Pending report file is empty, skipping"
        }
    } else {
        # No pending report - post a simple session end message
        Add-Content -Path $logFile -Value "[$timestamp] No pending report file found, posting session end message"

        $sessionEndMessage = "## Session End`n`nClaude Code session ended.`n`n---`nContext: $Context"

        Start-Process -FilePath "python" `
            -ArgumentList "`"$pythonScript`" `"$sessionEndMessage`"" `
            -NoNewWindow -Wait
    }

    # Notification sound
    [console]::beep(800, 200)

} catch {
    Add-Content -Path $logFile -Value "[$timestamp] Error: $_"
}

Write-Host "GitHub Issue Reporter v2 executed at $timestamp"
