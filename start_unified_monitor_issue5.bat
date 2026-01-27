@echo off
REM 統合版モニター起動 - Issue #5専用
REM upper:/lower:/ss コマンド対応

cd /d "%~dp0"

echo ========================================
echo 統合版 GitHub Issue #5 監視サービス
echo ========================================
echo.
echo 対応コマンド:
echo   - upper: テキスト  (画面上部に送信)
echo   - lower: テキスト  (画面下部に送信)
echo   - ss              (スクリーンショット撮影)
echo.
echo 監視対象: Tenormusica2024/Private Issue #5
echo.
echo Ctrl+Cで停止
echo ========================================
echo.

REM 統合版モニター実行
python unified_monitor.py

pause
