# GitHub Comment Monitor - PowerShell Launcher
# 永続バックグラウンド監視システム

param(
    [switch]$ShowStatus,
    [switch]$Stop,
    [switch]$Logs
)

# ディレクトリ設定
$WorkingDirectory = "C:\Users\Tenormusica\cc-snap-to-github"
$ServiceName = "GitHubCommentMonitor"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " GitHub Comment Monitor - PowerShell" -ForegroundColor Cyan  
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Working Directory: $WorkingDirectory" -ForegroundColor Yellow
Write-Host

# ディレクトリの存在確認
if (!(Test-Path $WorkingDirectory)) {
    Write-Host "❌ エラー: ディレクトリが見つかりません" -ForegroundColor Red
    Write-Host "   $WorkingDirectory" -ForegroundColor Red
    Write-Host
    Write-Host "正しいディレクトリを指定してください" -ForegroundColor Yellow
    exit 1
}

# ディレクトリに移動
Set-Location $WorkingDirectory

# ログディレクトリの作成
if (!(Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" -Force | Out-Null
    Write-Host "📁 ログディレクトリを作成しました: logs/" -ForegroundColor Green
}

# パラメータ処理
if ($ShowStatus) {
    Write-Host "📊 システム状態確認中..." -ForegroundColor Yellow
    Write-Host
    
    # Pythonプロセスの確認
    $processes = Get-Process | Where-Object { $_.ProcessName -eq "python" -and $_.CommandLine -like "*persistent_service.py*" }
    
    if ($processes) {
        Write-Host "✅ バックグラウンド監視サービス稼働中" -ForegroundColor Green
        foreach ($proc in $processes) {
            $uptime = (Get-Date) - $proc.StartTime
            Write-Host "   PID: $($proc.Id), 稼働時間: $($uptime.ToString('dd\.hh\:mm\:ss'))" -ForegroundColor Cyan
        }
    } else {
        Write-Host "⭕ バックグラウンド監視サービスは停止中" -ForegroundColor Yellow
    }
    
    # 最新ログの確認
    $latestLog = Get-ChildItem "logs\*.log" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($latestLog) {
        Write-Host
        Write-Host "📄 最新ログファイル: $($latestLog.Name)" -ForegroundColor Cyan
        Write-Host "   更新日時: $($latestLog.LastWriteTime)" -ForegroundColor Cyan
        Write-Host "   サイズ: $([math]::Round($latestLog.Length/1KB, 2)) KB" -ForegroundColor Cyan
    }
    
    # 状態ファイルの確認
    if (Test-Path ".gh_issue_to_claude_state.json") {
        $state = Get-Content ".gh_issue_to_claude_state.json" | ConvertFrom-Json
        Write-Host
        Write-Host "📋 処理状態:" -ForegroundColor Cyan
        Write-Host "   最終処理コメントID: $($state.last_comment_id)" -ForegroundColor Cyan
    }
    
    exit 0
}

if ($Stop) {
    Write-Host "⏹️ バックグラウンド監視サービスを停止中..." -ForegroundColor Yellow
    
    $processes = Get-Process | Where-Object { $_.ProcessName -eq "python" -and $_.CommandLine -like "*persistent_service.py*" }
    
    if ($processes) {
        foreach ($proc in $processes) {
            Write-Host "   PID $($proc.Id) を終了中..." -ForegroundColor Yellow
            Stop-Process -Id $proc.Id -Force
        }
        Write-Host "✅ バックグラウンドサービスを停止しました" -ForegroundColor Green
    } else {
        Write-Host "ℹ️ 停止対象のプロセスが見つかりません" -ForegroundColor Yellow
    }
    
    exit 0
}

if ($Logs) {
    Write-Host "📄 ログファイル一覧:" -ForegroundColor Yellow
    Write-Host
    
    $logFiles = Get-ChildItem "logs\*.log" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending
    
    if ($logFiles) {
        foreach ($log in $logFiles) {
            $sizeKB = [math]::Round($log.Length/1KB, 2)
            Write-Host "   $($log.Name)" -ForegroundColor Cyan
            Write-Host "     更新: $($log.LastWriteTime)" -ForegroundColor Gray
            Write-Host "     サイズ: $sizeKB KB" -ForegroundColor Gray
            Write-Host
        }
        
        Write-Host "最新ログを表示するには:" -ForegroundColor Yellow
        Write-Host "   Get-Content logs\$($logFiles[0].Name) -Tail 20" -ForegroundColor White
    } else {
        Write-Host "   ログファイルがありません" -ForegroundColor Yellow
    }
    
    exit 0
}

# デフォルト動作: バックグラウンドサービス開始
Write-Host "🚀 バックグラウンド監視サービスを開始します..." -ForegroundColor Green
Write-Host

# 既存プロセスの確認
$existingProcesses = Get-Process | Where-Object { $_.ProcessName -eq "python" -and $_.CommandLine -like "*persistent_service.py*" }

if ($existingProcesses) {
    Write-Host "⚠️ 既にバックグラウンドサービスが稼働中です" -ForegroundColor Yellow
    foreach ($proc in $existingProcesses) {
        $uptime = (Get-Date) - $proc.StartTime
        Write-Host "   PID: $($proc.Id), 稼働時間: $($uptime.ToString('dd\.hh\:mm\:ss'))" -ForegroundColor Cyan
    }
    Write-Host
    $choice = Read-Host "既存のプロセスを停止して新しく開始しますか？ (y/N)"
    
    if ($choice -eq "y" -or $choice -eq "Y") {
        Write-Host "既存プロセスを停止中..." -ForegroundColor Yellow
        foreach ($proc in $existingProcesses) {
            Stop-Process -Id $proc.Id -Force
        }
        Start-Sleep -Seconds 2
    } else {
        Write-Host "既存のサービスをそのまま使用します" -ForegroundColor Green
        exit 0
    }
}

# バックグラウンドでPythonサービスを開始
Write-Host "Python永続監視サービスを開始中..." -ForegroundColor Yellow

$processInfo = New-Object System.Diagnostics.ProcessStartInfo
$processInfo.FileName = "python"
$processInfo.Arguments = "persistent_service.py"
$processInfo.WorkingDirectory = $WorkingDirectory
$processInfo.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden
$processInfo.CreateNoWindow = $true
$processInfo.UseShellExecute = $false

$process = [System.Diagnostics.Process]::Start($processInfo)

if ($process) {
    Write-Host "✅ バックグラウンドサービス開始完了！" -ForegroundColor Green
    Write-Host "   プロセスID: $($process.Id)" -ForegroundColor Cyan
    Write-Host "   開始時刻: $(Get-Date)" -ForegroundColor Cyan
    Write-Host
    Write-Host "🎯 監視対象: GitHub Issue #3" -ForegroundColor Yellow
    Write-Host "⏱️ 監視間隔: 5秒" -ForegroundColor Yellow
    Write-Host "📁 ログ保存先: $WorkingDirectory\logs\" -ForegroundColor Yellow
    Write-Host
    Write-Host "システムコマンド:" -ForegroundColor White
    Write-Host "   状態確認: .\Start-BackgroundMonitor.ps1 -ShowStatus" -ForegroundColor Gray
    Write-Host "   ログ確認: .\Start-BackgroundMonitor.ps1 -Logs" -ForegroundColor Gray
    Write-Host "   停止: .\Start-BackgroundMonitor.ps1 -Stop" -ForegroundColor Gray
    Write-Host
    Write-Host "🎉 GitHub Issue #3のコメントが24時間365日自動処理されます！" -ForegroundColor Green
} else {
    Write-Host "❌ サービス開始に失敗しました" -ForegroundColor Red
    Write-Host "手動実行を試してください: python persistent_service.py" -ForegroundColor Yellow
}
