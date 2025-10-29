@echo off
echo ================================================
echo 🤖 Claude Code Task Complete (Private Repository)
echo ================================================
echo.

cd /d "C:\Users\Tenormusica\Documents\github-remote-desktop"

echo 📝 Posting task completion to private repository...
echo.

python task_complete_private.py %*

echo.
echo ✨ Private repository task completion process finished
echo ================================================
pause