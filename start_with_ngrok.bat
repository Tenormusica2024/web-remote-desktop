@echo off
echo Starting Remote Desktop Server with ngrok...
echo.

cd /d "C:\Users\Tenormusica\web-remote-desktop"

echo [1/2] Starting local server...
start /b python local_server.py --port 8094

echo Waiting for server to start...
timeout /t 5 /nobreak >nul

echo [2/2] Starting ngrok tunnel...
echo.
echo IMPORTANT: Copy the https URL that appears below
echo Use that URL on your smartphone!
echo.
ngrok http 8094