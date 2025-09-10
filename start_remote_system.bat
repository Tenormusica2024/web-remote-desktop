@echo off
cd /d "C:\Users\Tenormusica\cc-snap-to-github"

REM 環境変数設定
set GH_REPO=Tenormusica2024/web-remote-desktop
set GH_ISSUE=3
set GH_TOKEN=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
set POLL_SEC=5
set DEFAULT_PANE=lower
set ONLY_AUTHOR=Tenormusica2024

echo ========================================
echo  GitHub Issue to Claude Code System
echo ========================================
echo GH_REPO: %GH_REPO%
echo GH_ISSUE: %GH_ISSUE%
echo DEFAULT_PANE: %DEFAULT_PANE%
echo ONLY_AUTHOR: %ONLY_AUTHOR%
echo ========================================

echo.
echo システム開始中...
python gh_issue_to_claude_paste.py

pause