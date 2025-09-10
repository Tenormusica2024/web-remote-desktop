@echo off
cd /d "C:\Users\Tenormusica\cc-snap-to-github"

echo ========================================
echo  Persistent Comment Monitor Setup
echo ========================================

REM Create logs directory
if not exist logs mkdir logs

echo.
echo Setting up Windows Task Scheduler...
echo This will create a task that runs the monitor service automatically:
echo - Starts at Windows boot
echo - Runs 24/7 in background  
echo - Automatically restarts if it crashes
echo - Logs all activity to files
echo.

REM Create task with schtasks command
schtasks /create /tn "GitHubCommentMonitor" /tr "python \"%~dp0persistent_service.py\"" /sc onstart /ru "SYSTEM" /f

if %errorlevel% equ 0 (
    echo ✅ Task created successfully!
    echo.
    echo The monitor will now:
    echo - Start automatically when Windows boots
    echo - Run continuously in background
    echo - Monitor GitHub Issue #3 every 5 seconds
    echo - Process comments automatically
    echo - Log all activity to logs/ folder
    echo.
    echo To start immediately:
    echo   schtasks /run /tn "GitHubCommentMonitor"
    echo.
    echo To stop:
    echo   schtasks /end /tn "GitHubCommentMonitor"  
    echo.
    echo To remove:
    echo   schtasks /delete /tn "GitHubCommentMonitor" /f
) else (
    echo ❌ Failed to create task. Please run as Administrator.
    echo.
    echo Manual startup:
    echo   python persistent_service.py
)

echo.
echo ========================================
echo  Alternative: Manual Background Mode
echo ========================================
echo.
echo If Task Scheduler doesn't work, you can run manually:
echo   start /b python persistent_service.py
echo.
echo This will:
echo - Run in background immediately
echo - Continue after you close command prompt
echo - Keep running until computer restarts
echo.

pause