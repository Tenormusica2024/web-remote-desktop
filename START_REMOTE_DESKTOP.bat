@echo off
cls
echo.
echo ============================================================
echo    Remote Desktop System - Auto Start
echo ============================================================
echo.
echo Starting Remote Text Input System for Claude Code
echo.
echo Steps:
echo   1. Start server on this PC (automatic)
echo   2. Open browser on smartphone
echo   3. Access the displayed URL
echo   4. Type text and send to Claude Code
echo.
echo ============================================================
echo.

:: Change to the correct directory
cd /d "C:\Users\Tenormusica\web-remote-desktop"

:: Start server
echo [1/3] Starting local server...
start /b python local_server.py --port 8092

:: Wait for startup
echo Waiting for startup...
timeout /t 5 /nobreak >nul

:: Test connection
echo.
echo [2/3] Testing server...
curl -s http://localhost:8092/health >nul
if %errorlevel% equ 0 (
    echo Server started successfully
) else (
    echo Server startup failed
    pause
    exit /b 1
)

:: Simple completion message
echo.
echo [3/3] Setup complete!
echo.
echo ============================================================
echo    System Ready!
echo ============================================================
echo.
echo Access URLs for smartphone/tablet:
echo.
echo   Local: http://localhost:8092
echo   Network: http://192.168.3.3:8092
echo.
echo ============================================================
echo.
echo Usage:
echo   1. Open above URL on smartphone
echo   2. Type text in the textbox
echo   3. Click "Send Text" button
echo   4. Text will be typed in Claude Code terminal
echo.
echo Press Ctrl+C to stop the server
echo ============================================================
echo.

:: Open browser for testing
echo Opening test page...
start http://localhost:8092
echo.
echo Server is running. Test in browser.
echo.

:wait_loop
echo.
timeout /t 30 /nobreak >nul
echo Server still running... Press Ctrl+C to exit
goto wait_loop