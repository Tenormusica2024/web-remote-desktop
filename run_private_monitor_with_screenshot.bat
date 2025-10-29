@echo off
REM Private Issue Monitor + Screenshot Uploader 統合起動スクリプト
REM 2つのスクリプトを同時実行

echo ========================================
echo Private Issue Monitor + Screenshot System
echo ========================================
echo.

cd /d "C:\Users\Tenormusica\Documents\github-remote-desktop"

REM 設定確認
if not exist .env_private (
    echo [ERROR] .env_private が見つかりません
    pause
    exit /b 1
)

echo [INFO] 環境設定ファイル確認: OK
echo.

REM Python環境確認
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python が見つかりません
    pause
    exit /b 1
)

echo [INFO] Python環境確認: OK
echo.

REM 必要なライブラリ確認
echo [INFO] 必要なライブラリをチェック中...
python -c "import pyautogui, pyperclip, keyboard" >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] 一部のライブラリが不足しています
    echo [INFO] インストールを試行中...
    pip install pyautogui pyperclip keyboard >nul 2>&1
)

echo [INFO] ライブラリ確認: OK
echo.

REM 座標ファイル確認
if not exist .gh_issue_to_claude_coords_private_new.json (
    echo [ERROR] 座標ファイルが見つかりません: .gh_issue_to_claude_coords_private_new.json
    pause
    exit /b 1
)

echo [INFO] 座標ファイル確認: OK
echo.

echo ========================================
echo 2つのサービスを起動します:
echo 1. Private Issue Monitor Service
echo 2. Screenshot Uploader (Hotkey: Ctrl+Alt+F12)
echo ========================================
echo.
echo [!] 停止するには Ctrl+C を押してください
echo.

REM 2つのPythonスクリプトを別々のウィンドウで起動
start "Private Issue Monitor" python private_issue_monitor_service.py
timeout /t 2 /nobreak >nul

start "Screenshot Uploader" python pc-snap-uploader-private.py
timeout /t 2 /nobreak >nul

echo.
echo ========================================
echo [SUCCESS] 両サービスが起動しました
echo ========================================
echo.
echo [Monitor] Private Issue Monitor Service - 実行中
echo          - GitHub Issue のコメントを監視
echo          - "upper:" コマンド → Claude Code上部ペイン
echo          - "lower:" コマンド → Claude Code下部ペイン  
echo          - "ss" コマンド → スクリーンショット撮影・投稿
echo.
echo [Uploader] Screenshot Uploader - 実行中
echo           - ホットキー: Ctrl+Alt+F12
echo           - スクリーンショット即座撮影・アップロード
echo           - Private リポジトリに投稿
echo.
echo ログファイル:
echo - private_issue_monitor.log (Monitor)
echo - pc-snap-uploader.log (Uploader)
echo.
pause
