@echo off
chcp 65001 >nul 2>&1
color 0B
title GitHub Remote Control Systems - 状態確認

echo ============================================================
echo  📊 GitHub統合リモート制御システム 状態確認
echo ============================================================
echo  実行時刻: %date% %time%
echo.

:: プロセス状況確認
echo 🔍 実行中プロセス確認中...
echo.

set ss_count=0
set remote_count=0

for /f %%i in ('wmic process where "commandline like '%%real_time_monitor%%'" get processid 2^>nul ^| find /c /v ""') do set /a ss_count=%%i-1
for /f %%i in ('wmic process where "commandline like '%%gh_issue1_to_claude%%'" get processid 2^>nul ^| find /c /v ""') do set /a remote_count=%%i-1

echo ============================================================
echo  📋 システム状態サマリー
echo ============================================================
echo.

if %ss_count% gtr 0 (
    echo ✅ SSスクリーンショットシステム : %ss_count% プロセス稼働中
) else (
    echo ❌ SSスクリーンショットシステム : 停止中
)

if %remote_count% gtr 0 (
    echo ✅ Claude Codeリモート制御     : %remote_count% プロセス稼働中
) else (
    echo ❌ Claude Codeリモート制御     : 停止中
)

echo.
echo ============================================================
echo  🎯 動作概要
echo ============================================================
echo.

if %ss_count% gtr 0 (
    echo 📷 SS機能      : GitHub Issue #1に "ss" → 自動スクリーンショット投稿
    echo    監視間隔    : 10秒
    echo    自動停止    : 10時間後
)

if %remote_count% gtr 0 (
    echo 🎮 リモート制御 : "upper:/lower: メッセージ" → Claude Code自動入力
    echo    監視間隔    : 30秒
    echo    継続監視    : 無制限
)

echo.
echo ============================================================
echo  🛠️  管理コマンド
echo ============================================================
echo  起動 : start_github_remote.bat
echo  停止 : stop_github_remote.bat
echo  確認 : status_check.bat (このファイル)
echo.
echo  管理フォルダ: C:\Users\Tenormusica\GitHub-Remote-Control-Manager
echo.

:: プロセス詳細確認（オプション）
echo 詳細なプロセス情報を表示しますか？ (y/n)
set /p detail_choice=
if /i "%detail_choice%"=="y" (
    echo.
    echo ============================================================
    echo  🔧 詳細プロセス情報
    echo ============================================================
    echo.
    if %ss_count% gtr 0 (
        echo [SSシステム プロセス詳細]
        wmic process where "commandline like '%%real_time_monitor%%'" get processid,creationdate,commandline /format:list | findstr "ProcessId CreationDate CommandLine" 2>nul
        echo.
    )
    if %remote_count% gtr 0 (
        echo [リモート制御 プロセス詳細]
        wmic process where "commandline like '%%gh_issue1_to_claude%%'" get processid,creationdate,commandline /format:list | findstr "ProcessId CreationDate CommandLine" 2>nul
        echo.
    )
)

echo ============================================================
pause