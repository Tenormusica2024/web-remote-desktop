@echo off
echo Private Screenshot Uploaderを停止します...

tasklist /fi "WINDOWTITLE eq Private Screenshot*" /fo table
taskkill /f /im python.exe /fi "WINDOWTITLE eq Private Screenshot*"

if %errorlevel%==0 (
    echo Private Screenshot Uploaderを停止しました
) else (
    echo Private Screenshot Uploaderは実行されていませんでした
)

timeout /t 3