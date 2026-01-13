<#
.SYNOPSIS
    Auto-Report Previous Response Hook Script (v4 - Final)
.DESCRIPTION
    UserPromptSubmitイベント時に前回の回答をGitHub Issueに自動報告
    - pending_report.txtからの読み取りとtask_complete_private.pyの実行
    - プレースホルダー検出時はClaudeに警告を表示（Write-Host経由）
    - v4: ランダムGUIDサフィックス追加、UTF8NoBOM対応
#>

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$logDir = "C:\Users\Tenormusica\Documents\github-remote-desktop\logs"
$logFile = "$logDir\auto_report.log"
$pendingReportFile = "C:\Users\Tenormusica\Documents\github-remote-desktop\pending_report.txt"
$pythonScript = "C:\Users\Tenormusica\Documents\github-remote-desktop\task_complete_private.py"

# プレースホルダーの最小文字数
# 理由: "[PLACEHOLDER] Session started: 2026-01-13 16:45:00" ≈ 50文字
# 短い正当な報告（例: "了解しました"）は約20文字
# 100文字以下はプレースホルダーまたは極短報告として扱う
$placeholderThreshold = 100

# Ensure log directory exists
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

# Log execution start
Add-Content -Path $logFile -Value "[$timestamp] Auto-Report Hook triggered (UserPromptSubmit)"

try {
    # Check if pending report file exists
    if (Test-Path $pendingReportFile) {
        # Read the pending report content
        $reportContent = Get-Content -Path $pendingReportFile -Raw -Encoding UTF8
        $contentLength = if ($reportContent) { $reportContent.Trim().Length } else { 0 }

        if ($contentLength -gt $placeholderThreshold) {
            # 通常の報告処理: 内容がある場合
            Add-Content -Path $logFile -Value "[$timestamp] Found pending report, size: $contentLength chars"

            # ファイルベースで引数を渡す（特殊文字エスケープ問題を回避）
            # ランダムGUID追加で同時実行時の衝突を回避
            $randomSuffix = [guid]::NewGuid().ToString('N').Substring(0,8)
            $tempArgFile = Join-Path $env:TEMP "claude_report_arg_$(Get-Date -Format 'yyyyMMddHHmmss')_$randomSuffix.txt"
            # UTF8NoBOMで書き込み（BOMがあるとPythonで余分なバイトとして読まれる）
            [System.IO.File]::WriteAllText($tempArgFile, $reportContent, [System.Text.UTF8Encoding]::new($false))

            # Pythonスクリプトにファイルパスを渡す
            $process = Start-Process -FilePath "python" `
                -ArgumentList "`"$pythonScript`" --file `"$tempArgFile`"" `
                -NoNewWindow -Wait -PassThru `
                -RedirectStandardOutput "$logDir\python_stdout.log" `
                -RedirectStandardError "$logDir\python_stderr.log"

            Add-Content -Path $logFile -Value "[$timestamp] Python script exit code: $($process.ExitCode)"

            # Clean up temp file
            Remove-Item -Path $tempArgFile -Force -ErrorAction SilentlyContinue

            # Delete the pending report file after successful execution
            if ($process.ExitCode -eq 0) {
                Remove-Item -Path $pendingReportFile -Force
                Add-Content -Path $logFile -Value "[$timestamp] Pending report file deleted successfully"
            } else {
                Add-Content -Path $logFile -Value "[$timestamp] Python script failed, keeping pending report file"
                # 失敗時もClaudeに通知
                Write-Host ""
                Write-Host "=== GITHUB ISSUE REPORT FAILED ===" -ForegroundColor Red
                Write-Host "Python script failed with exit code: $($process.ExitCode)" -ForegroundColor Yellow
                Write-Host "Check logs: $logDir\python_stderr.log" -ForegroundColor Yellow
                Write-Host "==================================" -ForegroundColor Red
            }

        } elseif ($contentLength -gt 0) {
            # プレースホルダー検出: 短い内容（前回報告漏れの可能性）
            Add-Content -Path $logFile -Value "[$timestamp] WARNING: Placeholder file detected (size: $contentLength chars)"
            Add-Content -Path $logFile -Value "[$timestamp] WARNING: Previous session may have forgotten to report!"
            Add-Content -Path $logFile -Value "[$timestamp] Placeholder content: $($reportContent.Trim())"

            # Claudeに警告を表示（Write-Host出力はsystem-reminderとして表示される）
            Write-Host ""
            Write-Host "=== PREVIOUS REPORT FORGOTTEN ===" -ForegroundColor Red
            Write-Host "Placeholder detected: $($reportContent.Trim())" -ForegroundColor Yellow
            Write-Host "Previous session did NOT report to GitHub Issue!" -ForegroundColor Yellow
            Write-Host "Please check what happened and report manually if needed." -ForegroundColor Yellow
            Write-Host "==================================" -ForegroundColor Red

            # ファイルは残す（Claudeが確認後に削除）

        } else {
            # 完全に空のファイル
            Add-Content -Path $logFile -Value "[$timestamp] WARNING: Empty placeholder file detected"
            Add-Content -Path $logFile -Value "[$timestamp] WARNING: Previous session started but never reported!"

            # Claudeに警告を表示
            Write-Host ""
            Write-Host "=== EMPTY PLACEHOLDER DETECTED ===" -ForegroundColor Red
            Write-Host "Previous session created placeholder but NEVER reported!" -ForegroundColor Yellow
            Write-Host "This indicates a forgotten report. Check and report manually." -ForegroundColor Yellow
            Write-Host "==================================" -ForegroundColor Red

            # ファイルは残す
        }

    }
    # ファイルなしの場合は何も出力しない（ノイズ軽減）

} catch {
    Add-Content -Path $logFile -Value "[$timestamp] Error: $_"
    Write-Host ""
    Write-Host "=== AUTO-REPORT HOOK ERROR ===" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Yellow
    Write-Host "==============================" -ForegroundColor Red
}
