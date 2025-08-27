@echo off
echo.
echo ============================================================
echo    Cloud Run Remote Desktop Client - Auto Start
echo ============================================================
echo.
echo Starting connection to Cloud Run...
echo.
echo Web Interface: https://remote-desktop-ycqe3vmjva-uc.a.run.app
echo.
echo Instructions:
echo   1. This window will connect to Cloud Run
echo   2. Open the web interface above on your smartphone
echo   3. Turn ON Remote Mode in the web interface
echo   4. Type text and use Send Text button
echo.
echo ============================================================
echo.

cd /d "C:\Users\Tenormusica\web-remote-desktop"

echo Starting PC client...
python remote-client-cloudrun.py https://remote-desktop-ycqe3vmjva-uc.a.run.app

echo.
echo Connection ended.
pause