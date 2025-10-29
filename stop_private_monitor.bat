@echo off
echo Private Issue監視サービスを停止します...

tasklist /fi "WINDOWTITLE eq Private Issue Monitor*" /fo table
taskkill /f /im python.exe /fi "WINDOWTITLE eq Private Issue Monitor*"

if %errorlevel%==0 (
    echo Private Issue監視サービスを停止しました
) else (
    echo Private Issue監視サービスは実行されていませんでした
)

timeout /t 3
