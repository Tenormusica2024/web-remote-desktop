# GitHub Comment Monitor - Simple Version
param(
    [switch]$ShowStatus,
    [switch]$Stop,
    [switch]$Logs
)

$WorkingDirectory = "C:\Users\Tenormusica\cc-snap-to-github"

Write-Host "GitHub Comment Monitor" -ForegroundColor Cyan
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
    Write-Host "Checking system status..." -ForegroundColor Yellow
    $processes = Get-Process | Where-Object { $_.ProcessName -eq "python" -and $_.CommandLine -like "*persistent_service.py*" }
    
    if ($processes) {
        Write-Host "Background service is running" -ForegroundColor Green
        foreach ($proc in $processes) {
            $uptime = (Get-Date) - $proc.StartTime
            Write-Host "   PID: $($proc.Id), Uptime: $($uptime.ToString('dd\.hh\:mm\:ss'))" -ForegroundColor Cyan
        }
    } else {
        Write-Host "Background service is stopped" -ForegroundColor Yellow
    }
    exit 0
}

if ($Stop) {
    Write-Host "Stopping background service..." -ForegroundColor Yellow
    $processes = Get-Process | Where-Object { $_.ProcessName -eq "python" -and $_.CommandLine -like "*persistent_service.py*" }
    
    if ($processes) {
        foreach ($proc in $processes) {
            Write-Host "   Stopping PID $($proc.Id)..." -ForegroundColor Yellow
            Stop-Process -Id $proc.Id -Force
        }
        Write-Host "Background service stopped" -ForegroundColor Green
    } else {
        Write-Host "No processes found to stop" -ForegroundColor Yellow
    }
    exit 0
}

if ($Logs) {
    Write-Host "Log files:" -ForegroundColor Yellow
    $logFiles = Get-ChildItem "logs\*.log" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending
    
    if ($logFiles) {
        foreach ($log in $logFiles) {
            $sizeKB = [math]::Round($log.Length/1KB, 2)
            Write-Host "   $($log.Name) - $sizeKB KB - $($log.LastWriteTime)" -ForegroundColor Cyan
        }
    } else {
        Write-Host "   No log files found" -ForegroundColor Yellow
    }
    exit 0
}

# Default: Start background service
Write-Host "Starting background service..." -ForegroundColor Green

$existingProcesses = Get-Process | Where-Object { $_.ProcessName -eq "python" -and $_.CommandLine -like "*persistent_service.py*" }

if ($existingProcesses) {
    Write-Host "Background service already running" -ForegroundColor Yellow
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
        Write-Host "Using existing service" -ForegroundColor Green
        exit 0
    }
}

Write-Host "Starting Python service..." -ForegroundColor Yellow

$processInfo = New-Object System.Diagnostics.ProcessStartInfo
$processInfo.FileName = "python"
$processInfo.Arguments = "persistent_service.py"
$processInfo.WorkingDirectory = $WorkingDirectory
$processInfo.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden
$processInfo.CreateNoWindow = $true
$processInfo.UseShellExecute = $false

$process = [System.Diagnostics.Process]::Start($processInfo)

if ($process) {
    Write-Host "Background service started!" -ForegroundColor Green
    Write-Host "   Process ID: $($process.Id)" -ForegroundColor Cyan
    Write-Host "   Start time: $(Get-Date)" -ForegroundColor Cyan
    Write-Host
    Write-Host "Commands:" -ForegroundColor White
    Write-Host "   Status: .\Start-BackgroundMonitor.ps1 -ShowStatus" -ForegroundColor Gray
    Write-Host "   Logs: .\Start-BackgroundMonitor.ps1 -Logs" -ForegroundColor Gray
    Write-Host "   Stop: .\Start-BackgroundMonitor.ps1 -Stop" -ForegroundColor Gray
} else {
    Write-Host "Failed to start service" -ForegroundColor Red
    Write-Host "Try manual: python persistent_service.py" -ForegroundColor Yellow
}