@echo off
echo Private Screenshot Uploaderを開始します...

cd /d "C:\Users\Tenormusica\Documents\github-remote-desktop"

REM 既存のプロセスを停止
taskkill /f /im python.exe /fi "WINDOWTITLE eq Private Screenshot*" 2>nul

REM 新しいプロセスをバックグラウンドで開始
start "Private Screenshot Uploader" /min python pc-snap-uploader-private.py

echo Private Screenshot Uploaderがバックグラウンドで開始されました
echo ホットキー: Ctrl+Alt+F12 でスクリーンショットをPrivate repositoryに投稿
echo プロセスを停止するには: taskkill /f /im python.exe /fi "WINDOWTITLE eq Private Screenshot*"
echo 対象: Tenormusica2024/Private Issue #1

timeout /t 3