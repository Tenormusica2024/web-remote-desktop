# GitHub Issue #1 Comment Monitor - Management Script
param(
    [switch]$ShowStatus,
    [switch]$Stop,
    [switch]$Logs
)

$WorkingDirectory = "C:\Users\Tenormusica\cc-snap-to-github"

Write-Host "GitHub Issue #1 Comment Monitor" -ForegroundColor Cyan
Write-Host "Repository: Tenormusica2024/web-remote-desktop" -ForegroundColor Yellow
Write-Host "Issue: #1" -ForegroundColor Yellow
Write-Host "Commands: Only 'upper:' and 'lower:' prefixed comments" -ForegroundColor Green
Write-Host "Working Directory: $WorkingDirectory" -ForegroundColor Yellow
Write-Host

if (!(Test-Path $WorkingDirectory)) {
    Write-Host "Error: Directory not found" -ForegroundColor Red
    Write-Host "   $WorkingDirectory" -ForegroundColor Red
    exit 1
}

Set-Location $WorkingDirectory

if (!(Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" -Force | Out-Null
    Write-Host "Created logs directory" -ForegroundColor Green
}

if ($ShowStatus) {
    Write-Host "Checking Issue #1 monitor status..." -ForegroundColor Yellow
    $processes = Get-Process | Where-Object { $_.ProcessName -eq "python" -and $_.CommandLine -like "*persistent_service_issue1.py*" }
    
    if ($processes) {
        Write-Host "Issue #1 monitor is running" -ForegroundColor Green
        foreach ($proc in $processes) {
            $uptime = (Get-Date) - $proc.StartTime
            Write-Host "   PID: $($proc.Id), Uptime: $($uptime.ToString('dd\.hh\:mm\:ss'))" -ForegroundColor Cyan
        }
        
        # Show latest state
        $stateFile = ".gh_issue1_to_claude_state.json"
        if (Test-Path $stateFile) {
            $state = Get-Content $stateFile | ConvertFrom-Json
            Write-Host "   Last Comment ID: $($state.last_comment_id)" -ForegroundColor Cyan
        }
    } else {
        Write-Host "Issue #1 monitor is stopped" -ForegroundColor Yellow
    }
    exit 0
}

if ($Stop) {
    Write-Host "Stopping Issue #1 monitor..." -ForegroundColor Yellow
    $processes = Get-Process | Where-Object { $_.ProcessName -eq "python" -and $_.CommandLine -like "*persistent_service_issue1.py*" }
    
    if ($processes) {
        foreach ($proc in $processes) {
            Write-Host "   Stopping PID $($proc.Id)..." -ForegroundColor Yellow
            Stop-Process -Id $proc.Id -Force
        }
        Write-Host "Issue #1 monitor stopped" -ForegroundColor Green
    } else {
        Write-Host "No Issue #1 monitor processes found" -ForegroundColor Yellow
    }
    exit 0
}

if ($Logs) {
    Write-Host "Issue #1 monitor log files:" -ForegroundColor Yellow
    $logFiles = Get-ChildItem "logs\*issue1*.log" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending
    
    if ($logFiles) {
        foreach ($log in $logFiles) {
            $sizeKB = [math]::Round($log.Length/1KB, 2)
            Write-Host "   $($log.Name) - $sizeKB KB - $($log.LastWriteTime)" -ForegroundColor Cyan
        }
        
        Write-Host
        Write-Host "View latest log:" -ForegroundColor White
        $latestLog = $logFiles[0].Name
        Write-Host "   Get-Content logs\$latestLog -Tail 20" -ForegroundColor Gray
        Write-Host "   Get-Content logs\$latestLog -Tail 0 -Wait" -ForegroundColor Gray
    } else {
        Write-Host "   No Issue #1 log files found" -ForegroundColor Yellow
    }
    exit 0
}

# Default: Start Issue #1 monitor
Write-Host "Starting Issue #1 monitor..." -ForegroundColor Green

$existingProcesses = Get-Process | Where-Object { $_.ProcessName -eq "python" -and $_.CommandLine -like "*persistent_service_issue1.py*" }

if ($existingProcesses) {
    Write-Host "Issue #1 monitor already running" -ForegroundColor Yellow
    foreach ($proc in $existingProcesses) {
        $uptime = (Get-Date) - $proc.StartTime
        Write-Host "   PID: $($proc.Id), Uptime: $($uptime.ToString('dd\.hh\:mm\:ss'))" -ForegroundColor Cyan
    }
    $choice = Read-Host "Stop existing and start new? (y/N)"
    
    if ($choice -eq "y" -or $choice -eq "Y") {
        Write-Host "Stopping existing processes..." -ForegroundColor Yellow
        foreach ($proc in $existingProcesses) {
            Stop-Process -Id $proc.Id -Force
        }
        Start-Sleep -Seconds 2
    } else {
        Write-Host "Using existing Issue #1 monitor service" -ForegroundColor Green
        exit 0
    }
}

Write-Host "Starting Issue #1 Python service..." -ForegroundColor Yellow

$processInfo = New-Object System.Diagnostics.ProcessStartInfo
$processInfo.FileName = "python"
$processInfo.Arguments = "persistent_service_issue1.py"
$processInfo.WorkingDirectory = $WorkingDirectory
$processInfo.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden
$processInfo.CreateNoWindow = $true
$processInfo.UseShellExecute = $false

$process = [System.Diagnostics.Process]::Start($processInfo)

if ($process) {
    Write-Host "Issue #1 monitor started!" -ForegroundColor Green
    Write-Host "   Process ID: $($process.Id)" -ForegroundColor Cyan
    Write-Host "   Start time: $(Get-Date)" -ForegroundColor Cyan
    Write-Host "   Repository: Tenormusica2024/web-remote-desktop" -ForegroundColor Cyan
    Write-Host "   Issue: #1" -ForegroundColor Cyan
    Write-Host "   Processing: upper: and lower: commands only" -ForegroundColor Cyan
    Write-Host
    Write-Host "Commands:" -ForegroundColor White
    Write-Host "   Status: .\Start-Issue1Monitor.ps1 -ShowStatus" -ForegroundColor Gray
    Write-Host "   Logs: .\Start-Issue1Monitor.ps1 -Logs" -ForegroundColor Gray
    Write-Host "   Stop: .\Start-Issue1Monitor.ps1 -Stop" -ForegroundColor Gray
    Write-Host
    Write-Host "Test with GitHub comments:" -ForegroundColor White
    Write-Host "   upper: test message" -ForegroundColor Gray
    Write-Host "   lower: test message" -ForegroundColor Gray
    Write-Host "   (comments without prefix will be ignored)" -ForegroundColor Gray
} else {
    Write-Host "Failed to start Issue #1 service" -ForegroundColor Red
    Write-Host "Try manual: python persistent_service_issue1.py" -ForegroundColor Yellow
}