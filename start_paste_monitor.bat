@echo off
REM GitHub Issue #5 コメント監視→Claude Code送信サービス起動
REM upper: / lower: コマンドに対応

cd /d "%~dp0"

echo ========================================
echo GitHub Issue #5 監視サービス起動
echo ========================================
echo.
echo 監視対象: Tenormusica2024/Private Issue #5
echo 送信先: Claude Code (upper/lower対応)
echo.
echo Ctrl+Cで停止
echo ========================================
echo.

REM 監視スクリプト実行
python gh_issue_to_claude_paste_private_new.py

pause
