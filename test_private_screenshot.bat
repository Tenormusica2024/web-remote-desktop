@echo off
echo Private Screenshot Uploader動作テスト（1回のみ実行）...

cd /d "C:\Users\Tenormusica\Documents\github-remote-desktop"

python pc-snap-uploader-private.py --once --note "Test upload from Private screenshot uploader"

echo.
echo テスト完了。Private Issue #1を確認してください。
timeout /t 5