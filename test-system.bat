@echo off
setlocal
cd /d %~dp0

echo ===============================================
echo     Remote Screenshot System Test
echo ===============================================
echo.

echo Testing configuration...
if not exist ".env" (
    echo ERROR: .env file not found!
    echo Please configure .env first.
    pause
    exit /b 1
)

echo ✓ .env file exists

echo.
echo Testing Python dependencies...
python -c "import requests, pyautogui, keyboard; print('✓ All dependencies available')" 2>nul
if errorlevel 1 (
    echo Installing missing dependencies...
    python -m pip install -r requirements.txt
)

echo.
echo Testing GitHub connection...
python -c "
import os
from dotenv import load_dotenv
load_dotenv('.env')
token = os.getenv('GITHUB_TOKEN', '').strip()
repo = os.getenv('GITHUB_REPO', '').strip()
if not token or not repo:
    print('ERROR: GITHUB_TOKEN or GITHUB_REPO not configured')
    exit(1)
print('✓ GitHub configuration found')
"

if errorlevel 1 (
    echo Please configure GITHUB_TOKEN and GITHUB_REPO in .env
    pause
    exit /b 1
)

echo.
echo Available test options:
echo   1. Test screenshot capture only
echo   2. Test GitHub upload (creates actual file)
echo   3. Test remote monitoring (one check)
echo   4. Start full remote monitoring service
echo   5. Send test command (if you have office PC setup)
echo.

set /p choice="Enter choice (1-5): "

if "%choice%"=="1" (
    echo Testing screenshot capture...
    python -c "import pyautogui; shot = pyautogui.screenshot(); print(f'✓ Screenshot captured: {shot.size}')"
) else if "%choice%"=="2" (
    echo Testing GitHub upload...
    python remote-monitor.py --test
) else if "%choice%"=="3" (
    echo Testing remote monitoring (one check)...
    python remote-monitor.py --once
) else if "%choice%"=="4" (
    echo Starting remote monitoring service...
    .\start-remote-monitor.bat
) else if "%choice%"=="5" (
    echo Sending test command...
    python send-screenshot-command.py --note "System test"
) else (
    echo Invalid choice
    pause
    exit /b 1
)

echo.
echo Test completed!
pause