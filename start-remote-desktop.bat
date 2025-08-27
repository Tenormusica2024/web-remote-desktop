@echo off
echo ============================================================
echo Chrome Remote Desktop代替 - Web版リモートデスクトップ
echo ============================================================
echo.
echo 🚀 権限不要のリモートデスクトップシステム起動中...
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Pythonが見つかりません
    echo    Python 3.8以上をインストールしてください
    pause
    exit /b 1
)

echo ✅ Python確認済み

:: Install requirements
echo 📦 必要なライブラリをインストール中...
pip install -r requirements.txt --quiet --user

if %errorlevel% neq 0 (
    echo ⚠️  一部ライブラリのインストールに失敗しました
    echo    続行しますが、エラーが発生する可能性があります
)

echo ✅ ライブラリインストール完了

:: Start server
echo.
echo 🌐 Webサーバー起動中...
echo    アクセスURL: http://localhost:8080
echo    LAN内アクセス: http://192.168.3.3:8080
echo.
echo 💡 使用方法:
echo    1. ブラウザが自動で開きます
echo    2. 画面をクリック・操作してリモートPC操作
echo    3. テキスト入力は下部のテキストボックスから
echo    4. Ctrl+C でサーバー停止
echo.
echo ⚠️  セキュリティ注意:
echo    - ローカルネットワーク内でのみ使用
echo    - 社内環境からのアクセス時は十分注意
echo.
echo ============================================================

:: Start Python server
python app-simple.py

echo.
echo サーバーが停止しました
pause