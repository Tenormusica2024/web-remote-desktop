@echo off
setlocal enabledelayedexpansion

echo ===============================================
echo    Remote Screenshot Command Sender
echo    (for Office PC → Home PC via GitHub)
echo ===============================================
echo.

REM 簡易設定確認
if "%GITHUB_TOKEN%"=="" (
    echo ERROR: GITHUB_TOKEN environment variable is not set!
    echo Please set your GitHub token first:
    echo   set GITHUB_TOKEN=ghp_your_token_here
    echo   set GITHUB_REPO=owner/repo-name
    pause
    exit /b 1
)

if "%GITHUB_REPO%"=="" (
    echo ERROR: GITHUB_REPO environment variable is not set!
    echo Please set: set GITHUB_REPO=owner/repo-name
    pause
    exit /b 1
)

echo Current settings:
echo   Repository: %GITHUB_REPO%
echo   Issue: %MONITOR_ISSUE_NUMBER%
echo.

echo Select screenshot request type:
echo   1. Normal screenshot
echo   2. Urgent screenshot  
echo   3. Screenshot with note
echo   4. Custom command
echo.

set /p choice="Enter choice (1-4): "

if "%choice%"=="1" (
    python send-screenshot-command.py
) else if "%choice%"=="2" (
    python send-screenshot-command.py --urgent
) else if "%choice%"=="3" (
    set /p note="Enter note: "
    python send-screenshot-command.py --note "!note!"
) else if "%choice%"=="4" (
    set /p custom="Enter custom command: "
    python send-screenshot-command.py --message "!custom!"
) else (
    echo Invalid choice!
    pause
    exit /b 1
)

echo.
pause