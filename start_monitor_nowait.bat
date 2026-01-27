@echo off
cd /d "%~dp0"
start "GitHub Issue #5 Monitor" /min cmd /c "python unified_monitor.py > monitor_output.log 2>&1"
echo 監視スクリプトをバックグラウンドで起動しました
echo ログファイル: monitor_output.log
timeout /t 2
