@echo off
setlocal
cd /d %~dp0

echo Starting remote screenshot monitor...

REM 依存をインストール（初回のみ）
echo Checking dependencies...
python -m pip install -r requirements.txt > nul 2>&1

REM バックグラウンドで監視サービス開始
echo Starting background monitor (Issue monitoring)...
start "" /min python remote-monitor.py

REM ログ表示用（別ウィンドウ）
timeout /t 2 > nul
if exist monitor.log (
    echo Opening log viewer...
    start "" /min powershell -Command "Get-Content -Path 'monitor.log' -Wait -Tail 10"
)

echo Remote monitor started!
echo Check monitor.log for activity.
echo To stop: close the python process or press Ctrl+C in the monitor window.
pause