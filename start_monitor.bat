@echo off
echo Starting GitHub Remote Desktop Screenshot Monitor...
echo Monitor will run for 10 hours (36000 seconds)
echo Press Ctrl+C to stop manually

cd /d "C:\Users\Tenormusica\Documents\github-remote-desktop"

echo Starting background monitoring...
start "GitHub Monitor" /MIN python remote-monitor.py

echo Monitor started in background window
echo Check monitor.log for activity
echo Use stop_monitor.bat to stop the service

timeout /t 3
echo.
echo Monitor is now running. You can close this window.
pause