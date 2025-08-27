@echo off
REM Claude Code Remote Desktop - Auto Start Client
REM This script automatically starts the PC client
chcp 65001 > nul

echo [AUTO START] Claude Code Remote Desktop Client
echo Starting in 3 seconds...
powershell "Start-Sleep 3"

cd /d "C:\Users\Tenormusica\web-remote-desktop"

:RESTART
echo [AUTO START] Starting final stable remote desktop client...
python final_stable_client.py

echo [AUTO START] Client stopped. Restarting in 5 seconds...
powershell "Start-Sleep 5"
goto RESTART