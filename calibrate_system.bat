@echo off
cd /d "C:\Users\Tenormusica\cc-snap-to-github"

REM 環境変数設定
set GH_REPO=Tenormusica2024/Private
set GH_ISSUE=1
set GH_TOKEN=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
set POLL_SEC=5
set DEFAULT_PANE=lower
set ONLY_AUTHOR=Tenormusica2024

echo ========================================
echo  キャリブレーション開始
echo ========================================
echo.
echo 手順:
echo 1. Claude Codeアプリを開いてください
echo 2. 右上と右下の入力欄が見える状態にしてください  
echo 3. このウィンドウに戻って続行してください
echo.
pause

echo キャリブレーション実行中...
python gh_issue_to_claude_paste.py --calibrate

pause