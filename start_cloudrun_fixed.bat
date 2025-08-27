@echo off
echo ============================================================
echo    Cloud Run Remote Desktop Client - Fixed Version
echo ============================================================
echo.
echo Starting connection to Cloud Run...
echo.
echo Web Interface: https://remote-desktop-ycqe3vmjva-uc.a.run.app
echo.
echo Instructions:
echo   1. This window connects to Cloud Run
echo   2. Open web interface on smartphone
echo   3. Turn ON Remote Mode
echo   4. PC screen will be shared automatically
echo.
echo ============================================================
echo.

cd /d "C:\Users\Tenormusica\web-remote-desktop"

echo Starting Cloud Run client...
python remote-desktop-client.py

echo.
echo Client stopped.
pause