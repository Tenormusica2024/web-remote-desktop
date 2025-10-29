@echo off
echo ================================================
echo 🤖 Claude Code Universal Monitor (Public/Private)
echo ================================================
echo.

cd /d "C:\Users\Tenormusica\Documents\github-remote-desktop"

echo 🔍 Detecting repository type and starting monitors...
echo.

echo 📋 Available configurations:
if exist ".env" (
    echo   ✅ .env found - Public repository configuration
) else (
    echo   ❌ .env not found
)

if exist ".env_private" (
    echo   ✅ .env_private found - Private repository configuration  
) else (
    echo   ❌ .env_private not found
)

echo.
echo 🚀 Starting all available monitors...
echo.

REM Public repository monitors (if .env exists)
if exist ".env" (
    echo 1. Starting Public Screenshot Monitor...
    start "Public Screenshot Monitor" /MIN python real_time_monitor.py
    
    echo 2. Starting Public Title Monitor...
    start "Public Title Monitor" /MIN python remote-monitor.py
    echo   ✅ Public repository monitors started
) else (
    echo   ⚠️  Public configuration (.env) not found - skipping public monitors
)

echo.

REM Private repository monitors (if .env_private exists)
if exist ".env_private" (
    echo 3. Starting Private Screenshot Monitor...
    start "Private Screenshot Monitor" /MIN python real_time_monitor_private.py
    
    echo 4. Starting Private Title Monitor...
    start "Private Title Monitor" /MIN python remote-monitor_private.py
    echo   ✅ Private repository monitors started
) else (
    echo   ⚠️  Private configuration (.env_private) not found - skipping private monitors
)

echo.
echo ================================================
echo ✨ Universal monitor startup complete!
echo.
echo 📊 Active monitors:
echo   - Public monitors: %PUBLIC_COUNT% (if .env exists)
echo   - Private monitors: %PRIVATE_COUNT% (if .env_private exists)
echo.
echo 📝 Log files:
echo   - Public: realtime_monitor.log, monitor.log
echo   - Private: realtime_monitor_private.log, monitor_private.log
echo.
echo 💡 Note: Monitors will auto-start based on available config files
echo ================================================
pause