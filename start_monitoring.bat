@echo off
echo === GitHub Remote Desktop Monitor ===
echo.
echo Starting remote screenshot monitoring system...
echo Repository: Tenormusica2024/web-remote-desktop
echo Issue: #1
echo.

cd /d "%~dp0"

REM Python環境チェック
python --version
if errorlevel 1 (
    echo ERROR: Python not found
    pause
    exit /b 1
)

REM 依存関係チェック
echo Checking dependencies...
python -c "import requests, pyautogui, keyboard, dotenv; print('All dependencies OK')"
if errorlevel 1 (
    echo ERROR: Missing dependencies. Run: pip install -r requirements.txt
    pause
    exit /b 1
)

REM 設定チェック
echo Checking configuration...
python test_github_access.py
if errorlevel 1 (
    echo.
    echo ERROR: GitHub token configuration failed
    echo Please run: python setup_new_token.py
    pause
    exit /b 1
)

echo.
echo === Starting Remote Monitor ===
echo Press Ctrl+C to stop monitoring
echo.

python remote-monitor.py