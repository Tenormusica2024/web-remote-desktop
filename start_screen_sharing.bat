@echo off
cls
echo.
echo ============================================================
echo    🖥️ Remote Desktop - Screen Sharing Client
echo ============================================================
echo.
echo Starting screen sharing connection to Cloud Run...
echo.
echo Web Interface: https://remote-desktop-ycqe3vmjva-uc.a.run.app
echo.
echo Features:
echo   ✅ Screen sharing (real-time)
echo   ✅ Remote text input to Claude Code
echo   ✅ Click control
echo   ✅ Keyboard shortcuts (Ctrl+C/V, Enter)
echo   ✅ Corporate network friendly
echo.
echo Instructions:
echo   1. This window will connect to Cloud Run
echo   2. Open the web interface above on your smartphone
echo   3. Wait for "PC client connected ✅"
echo   4. Turn ON Remote Mode (⚠️ OFF → ✅ ON)
echo   5. You can now see and control your PC screen!
echo.
echo ============================================================
echo.

cd /d "C:\Users\Tenormusica\web-remote-desktop"

echo 🔄 Starting enhanced client with screen sharing...
echo.
python remote-desktop-client.py

echo.
echo 🛑 Screen sharing stopped.
pause