@echo off
echo Stopping GitHub Remote Desktop Screenshot Monitor...

echo Killing all python processes running remote-monitor.py...
taskkill /f /im python.exe /fi "WINDOWTITLE eq GitHub Monitor*" 2>nul
if errorlevel 1 (
    echo No active monitor processes found
) else (
    echo Monitor processes terminated
)

echo.
echo Monitor has been stopped.
pause