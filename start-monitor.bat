@echo off
REM GitHub Issue Monitor SubAgent 起動スクリプト
REM バックグラウンドで監視サブエージェントを起動

echo ========================================
echo GitHub Issue Monitor SubAgent
echo ========================================
echo.
echo 監視サブエージェントを起動します...
echo.

REM プロセス起動
start /min python "%~dp0github-issue-monitor-subagent.py"

echo 監視サブエージェントがバックグラウンドで起動しました
echo.
echo [監視設定]
echo - チェック間隔: 30秒
echo - 応答タイムアウト: 2分
echo - 対象: GitHub Issue #5
echo.
echo 停止するには、タスクマネージャーから
echo python.exe (github-issue-monitor-subagent.py) を終了してください
echo.
pause