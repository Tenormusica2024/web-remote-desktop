@echo off
REM GitHub Issue Monitor SubAgent 停止スクリプト

echo ========================================
echo GitHub Issue Monitor SubAgent 停止
echo ========================================
echo.

REM Pythonプロセスから監視スクリプトを探して停止
for /f "tokens=2" %%i in ('wmic process where "commandline like '%%github-issue-monitor-subagent%%'" get processid /value ^| find "="') do (
    echo プロセス %%i を停止します...
    taskkill /F /PID %%i
)

echo.
echo 監視サブエージェントを停止しました
echo.
pause