@echo off
cd /d "C:\Users\Tenormusica\cc-snap-to-github"

echo ========================================
echo  Forever Background Comment Monitor
echo ========================================
echo Start time: %date% %time%
echo.

REM Create logs directory
if not exist logs mkdir logs

echo Starting persistent monitoring service...
echo This will run FOREVER in background until manually stopped.
echo.
echo Features:
echo - 24/7 monitoring
echo - Auto-restart on errors  
echo - Detailed logging
echo - Process comments instantly
echo.
echo To stop: Press Ctrl+C or close this window
echo Log files: check logs/ folder
echo.

REM Start the persistent service in background
start /min "GitHub Comment Monitor" cmd /c "python persistent_service.py"

echo ✅ Background service started!
echo.
echo The monitor is now running invisibly in background.
echo Check logs/ folder for activity.
echo.
echo Status check commands:
echo   tasklist | findstr python
echo   dir logs\*.log
echo.

pause