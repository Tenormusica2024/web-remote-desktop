# Watchdog Monitor Windowsタスクスケジューラ登録

$taskName = "GitHubIssueWatchdog"
$scriptPath = "C:\Users\Tenormusica\Documents\github-remote-desktop\watchdog_monitor_service.py"
$pythonExe = (Get-Command python).Path

Write-Host "==========================================="
Write-Host "Watchdog Monitor Task Setup"
Write-Host "==========================================="
Write-Host "Task Name: $taskName"
Write-Host "Script: $scriptPath"
Write-Host "Python: $pythonExe"
Write-Host ""

# Delete existing task if exists
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "[INFO] Removing existing task..."
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    Write-Host "[OK] Existing task removed"
}

# Create task action
$action = New-ScheduledTaskAction -Execute $pythonExe -Argument $scriptPath

# Create task trigger (every 5 minutes)
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 5)

# Task settings
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# Register task
Write-Host "[INFO] Registering task..."
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Description "GitHub Issue Monitor Watchdog (every 5 minutes)"

Write-Host "[OK] Task registered successfully"
Write-Host ""

# Show task info
Write-Host "==========================================="
Write-Host "Registered Task Information"
Write-Host "==========================================="
Get-ScheduledTask -TaskName $taskName | Format-List TaskName,State,TaskPath

Write-Host ""
Write-Host "==========================================="
Write-Host "Next Run Time"
Write-Host "==========================================="
$task = Get-ScheduledTask -TaskName $taskName
$taskInfo = $task | Get-ScheduledTaskInfo
Write-Host "Next run: $($taskInfo.NextRunTime)"
Write-Host ""
Write-Host "[OK] Setup completed"
Write-Host ""
Write-Host "To verify: taskschd.msc"
Write-Host "To run manually: Start-ScheduledTask -TaskName $taskName"
Write-Host ""