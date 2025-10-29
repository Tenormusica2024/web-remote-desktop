@echo off
chcp 65001 >nul
echo ================================================
echo Claude Code Private Repository Remote Control
echo Target: Tenormusica2024/Private Issue #1
echo ================================================
echo.

cd /d "C:\Users\Tenormusica\Documents\github-remote-desktop"

echo Starting Private Repository remote control systems...
echo.

echo 1. Configuration Check...
if exist ".env_private" (
    echo   OK - Private repository configuration found
) else (
    echo   ERROR - .env_private not found
    pause
    exit /b 1
)

echo.
echo 2. Starting Private Repository Monitors...
echo.

echo   a) Screenshot Monitor (Private)...
start "Private Screenshot Monitor" /MIN python real_time_monitor_private.py
timeout /t 2 /nobreak >nul

echo   b) Title Change Monitor (Private)...
start "Private Title Monitor" /MIN python remote-monitor_private.py
timeout /t 2 /nobreak >nul

echo.
echo ================================================
echo READY: Private Repository Remote Control Active
echo.
echo Target Repository: Tenormusica2024/Private
echo Issue Number: #1
echo.
echo Commands available:
echo   - Post "ss" in comments for screenshot
echo   - Change title to include "ss" for screenshot
echo.
echo Log files:
echo   - realtime_monitor_private.log
echo   - monitor_private.log
echo.
echo Press Ctrl+C to stop monitoring
echo ================================================
pause