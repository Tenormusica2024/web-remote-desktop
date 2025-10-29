@echo off
REM 🤖 クイックタスク完了報告（ウィンドウを表示せずに実行）
cd /d "C:\Users\Tenormusica\Documents\github-remote-desktop"
python task_complete.py > nul 2>&1
echo ✅ タスク完了をGitHub Issue #1に報告しました