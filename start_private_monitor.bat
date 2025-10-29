@echo off
echo Private Issue監視サービスをバックグラウンドで開始します...

cd /d "C:\Users\Tenormusica\Documents\github-remote-desktop"

REM 既存のプロセスを停止
taskkill /f /im python.exe /fi "WINDOWTITLE eq Private Issue Monitor*" 2>nul

REM 新しいプロセスをバックグラウンドで開始
start "Private Issue Monitor Service" /min python private_issue_monitor_service.py

echo Private Issue監視サービスがバックグラウンドで開始されました
echo プロセスを停止するには: taskkill /f /im python.exe /fi "WINDOWTITLE eq Private Issue Monitor*"
echo ログファイル: private_issue_monitor.log

timeout /t 3
