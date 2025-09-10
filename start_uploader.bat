@echo off
setlocal
cd /d %~dp0
REM プロキシが必要ならここで一時設定:
REM set HTTP_PROXY=http://user:pass@proxy:8080
REM set HTTPS_PROXY=http://user:pass@proxy:8080

REM 依存をインストール（初回のみ）
echo Installing dependencies...
python -m pip install -r requirements.txt

REM ホットキー常駐（Ctrl+Alt+F12 既定）
echo Starting screenshot uploader...
start "" /min python pc-snap-uploader.py
echo Started. Press the hotkey to send a screenshot. (Ctrl+Alt+F12)
pause