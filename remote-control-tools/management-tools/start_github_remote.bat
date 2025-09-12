@echo off
chcp 65001 >nul 2>&1
color 0A
title GitHub Remote Control Systems - 統合起動

echo ============================================================
echo  🚀 GitHub統合リモート制御システム 一括起動
echo ============================================================
echo  実行時刻: %date% %time%
echo.
echo  起動するシステム:
echo  1. SSスクリーンショット投稿システム (10秒間隔)
echo  2. Claude Codeリモート制御システム (30秒間隔)
echo.
echo ============================================================
echo.

:: 既存プロセス確認
echo 📊 既存プロセス確認中...
wmic process where "commandline like '%%real_time_monitor%%'" get processid 2>nul | find /c /v "" >nul
if %errorlevel% neq 1 (
    echo ⚠️  既存のSSシステムプロセスが実行中です
    echo.
)

wmic process where "commandline like '%%gh_issue1_to_claude%%'" get processid 2>nul | find /c /v "" >nul  
if %errorlevel% neq 1 (
    echo ⚠️  既存のリモート制御プロセスが実行中です
    echo.
)

:: SSスクリーンショットシステム起動
echo 🎯 [1/2] SSスクリーンショット投稿システム起動中...
cd /d "C:\Users\Tenormusica\Documents\github-remote-desktop"
start /b "" cmd /c python real_time_monitor.py >nul 2>&1
timeout /t 2 /nobreak >nul
echo ✅ SSシステム起動コマンド実行完了
echo.

:: Claude Codeリモート制御システム起動
echo 🎯 [2/2] Claude Codeリモート制御システム起動中...
cd /d "C:\Users\Tenormusica\cc-snap-to-github"
start /b "" cmd /c python gh_issue1_to_claude_paste.py --interval 30 >nul 2>&1
timeout /t 2 /nobreak >nul
echo ✅ リモート制御システム起動コマンド実行完了
echo.

:: 起動確認
echo ============================================================
echo  🔍 起動確認
echo ============================================================
timeout /t 3 /nobreak >nul

:: プロセス数カウント
set ss_count=0
set remote_count=0

for /f %%i in ('wmic process where "commandline like '%%real_time_monitor%%'" get processid 2^>nul ^| find /c /v ""') do set /a ss_count=%%i-1
for /f %%i in ('wmic process where "commandline like '%%gh_issue1_to_claude%%'" get processid 2^>nul ^| find /c /v ""') do set /a remote_count=%%i-1

echo  SSシステム       : %ss_count% プロセス稼働中
echo  リモート制御     : %remote_count% プロセス稼働中
echo.

if %ss_count% gtr 0 if %remote_count% gtr 0 (
    echo 🎉 両システム正常起動完了！
) else (
    echo ⚠️  一部システムの起動に失敗した可能性があります
)

echo.
echo ============================================================
echo  📝 使用方法
echo ============================================================
echo  1. GitHub Issue #1に "ss" → スクリーンショット自動投稿
echo  2. "upper: メッセージ" → Claude Code上部ペインに入力
echo  3. "lower: メッセージ" → Claude Code下部ペインに入力
echo.
echo  停止: stop_github_remote.bat を実行
echo  管理フォルダ: C:\Users\Tenormusica\GitHub-Remote-Control-Manager
echo ============================================================
echo.
pause