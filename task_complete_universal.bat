@echo off
chcp 65001 >nul
echo ================================================
echo Claude Code Universal Task Complete Report
echo ================================================
echo:

cd /d "C:\Users\Tenormusica\Documents\github-remote-desktop"

echo Detecting available repository configurations...
echo:

set PUBLIC_AVAILABLE=0
set PRIVATE_AVAILABLE=0

if exist ".env" (
    echo   Public repository configuration found (.env)
    set PUBLIC_AVAILABLE=1
)

if exist ".env_private" (
    echo   Private repository configuration found (.env_private)
    set PRIVATE_AVAILABLE=1
)

if %PUBLIC_AVAILABLE%==0 if %PRIVATE_AVAILABLE%==0 (
    echo   No repository configurations found!
    echo   Please create .env or .env_private file first.
    echo.
    pause
    exit /b 1
)

echo:
echo Posting task completion reports...
echo:

REM Post to public repository first (priority)
if %PUBLIC_AVAILABLE%==1 (
    echo 1. Posting to Public Repository (Primary)...
    python task_complete.py %*
    echo:
)

REM Post to private repository only if public not available
if %PUBLIC_AVAILABLE%==0 if %PRIVATE_AVAILABLE%==1 (
    echo 2. Posting to Private Repository (Fallback)...
    python task_complete_private.py %*
    echo:
)

echo ================================================
echo Universal task completion reports sent!
echo:
echo Reports sent to:
if %PUBLIC_AVAILABLE%==1 (
    echo   - Public repository: OK
)
if %PRIVATE_AVAILABLE%==1 if %PUBLIC_AVAILABLE%==0 (
    echo   - Private repository: OK
)
echo:
echo Note: Reports posted to all available repositories
echo ================================================
pause