@echo off
chcp 65001 >nul 2>&1
color 0C
title GitHub Remote Control Systems - 停止

echo ============================================================
echo  🛑 GitHub統合リモート制御システム 停止
echo ============================================================
echo  実行時刻: %date% %time%
echo.

:: プロセス確認
echo 📊 実行中プロセス確認...
echo.

set ss_count=0
set remote_count=0

for /f %%i in ('wmic process where "commandline like '%%real_time_monitor%%'" get processid 2^>nul ^| find /c /v ""') do set /a ss_count=%%i-1
for /f %%i in ('wmic process where "commandline like '%%gh_issue1_to_claude%%'" get processid 2^>nul ^| find /c /v ""') do set /a remote_count=%%i-1

echo  SSシステム       : %ss_count% プロセス
echo  リモート制御     : %remote_count% プロセス
echo.

if %ss_count% equ 0 if %remote_count% equ 0 (
    echo ℹ️  実行中のプロセスはありません
    echo.
    pause
    exit /b 0
)

echo ============================================================
echo  🔧 プロセス停止中...
echo ============================================================
echo.

:: SSシステム停止
if %ss_count% gtr 0 (
    echo [1/2] SSスクリーンショットシステム停止中...
    wmic process where "commandline like '%%real_time_monitor%%'" delete >nul 2>&1
    timeout /t 1 /nobreak >nul
    echo ✅ SSシステム停止完了
) else (
    echo [1/2] SSシステムは実行されていません
)
echo.

:: リモート制御システム停止
if %remote_count% gtr 0 (
    echo [2/2] Claude Codeリモート制御システム停止中...
    wmic process where "commandline like '%%gh_issue1_to_claude%%'" delete >nul 2>&1
    timeout /t 1 /nobreak >nul
    echo ✅ リモート制御システム停止完了
) else (
    echo [2/2] リモート制御システムは実行されていません
)
echo.

:: 停止確認
echo ============================================================
echo  🔍 停止確認
echo ============================================================
timeout /t 2 /nobreak >nul

set ss_count_after=0
set remote_count_after=0

for /f %%i in ('wmic process where "commandline like '%%real_time_monitor%%'" get processid 2^>nul ^| find /c /v ""') do set /a ss_count_after=%%i-1
for /f %%i in ('wmic process where "commandline like '%%gh_issue1_to_claude%%'" get processid 2^>nul ^| find /c /v ""') do set /a remote_count_after=%%i-1

echo.
echo  停止後のプロセス数:
echo  SSシステム       : %ss_count_after% プロセス
echo  リモート制御     : %remote_count_after% プロセス
echo.

if %ss_count_after% equ 0 if %remote_count_after% equ 0 (
    echo 🎉 全プロセス正常停止完了！
) else (
    echo ⚠️  一部プロセスの停止に失敗しました
    echo    タスクマネージャーで手動確認してください
)

echo.
echo  管理フォルダ: C:\Users\Tenormusica\GitHub-Remote-Control-Manager
echo ============================================================
echo.
pause