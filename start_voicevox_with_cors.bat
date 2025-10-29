@echo off
chcp 65001 > nul
echo VOICEVOXをCORS許可モードで起動します...

REM VOICEVOXの実行ファイルパスを探す
set "VOICEVOX_PATH="

REM 一般的なインストール先を確認
if exist "C:\Program Files\VOICEVOX\VOICEVOX.exe" (
    set "VOICEVOX_PATH=C:\Program Files\VOICEVOX\VOICEVOX.exe"
)
if exist "C:\Program Files (x86)\VOICEVOX\VOICEVOX.exe" (
    set "VOICEVOX_PATH=C:\Program Files (x86)\VOICEVOX\VOICEVOX.exe"
)
if exist "%LOCALAPPDATA%\Programs\VOICEVOX\VOICEVOX.exe" (
    set "VOICEVOX_PATH=%LOCALAPPDATA%\Programs\VOICEVOX\VOICEVOX.exe"
)

if "%VOICEVOX_PATH%"=="" (
    echo ❌ VOICEVOXが見つかりません
    echo VOICEVOXのインストール先を手動で指定してください
    pause
    exit /b 1
)

echo ✓ VOICEVOX検出: %VOICEVOX_PATH%
echo.
echo CORS許可モードで起動中...
start "" "%VOICEVOX_PATH%" --cors_policy_mode=all

timeout /t 3 > nul
echo.
echo ✅ VOICEVOX起動完了
echo ブラウザを再読み込みして音声通知をテストしてください
pause
