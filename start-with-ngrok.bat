@echo off
echo ============================================================
echo LOCAL REMOTE DESKTOP WITH NGROK
echo ============================================================
echo.
echo Starting local server on port 8091...
start /b python local_server.py --port 8091

echo.
echo Waiting for server to start...
timeout /t 3 /nobreak >nul

echo.
echo Starting ngrok tunnel...
echo.
echo NOTE: If ngrok is not installed, download from:
echo       https://ngrok.com/download
echo.
ngrok http 8091

pause