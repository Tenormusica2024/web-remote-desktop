@echo off
chcp 65001 > nul
echo VOICEVOX繧辰ORS險ｱ蜿ｯ繝｢繝ｼ繝峨〒襍ｷ蜍輔＠縺ｾ縺・..

REM VOICEVOX縺ｮ螳溯｡後ヵ繧｡繧､繝ｫ繝代せ繧呈爾縺・set "VOICEVOX_PATH="

REM 荳闊ｬ逧・↑繧､繝ｳ繧ｹ繝医・繝ｫ蜈医ｒ遒ｺ隱・if exist "C:\Program Files\VOICEVOX\VOICEVOX.exe" (
    set "VOICEVOX_PATH=C:\Program Files\VOICEVOX\VOICEVOX.exe"
)
if exist "C:\Program Files (x86)\VOICEVOX\VOICEVOX.exe" (
    set "VOICEVOX_PATH=C:\Program Files (x86)\VOICEVOX\VOICEVOX.exe"
)
if exist "%LOCALAPPDATA%\Programs\VOICEVOX\VOICEVOX.exe" (
    set "VOICEVOX_PATH=%LOCALAPPDATA%\Programs\VOICEVOX\VOICEVOX.exe"
)

if "%VOICEVOX_PATH%"=="" (
    echo 笶・VOICEVOX縺瑚ｦ九▽縺九ｊ縺ｾ縺帙ｓ
    echo VOICEVOX縺ｮ繧､繝ｳ繧ｹ繝医・繝ｫ蜈医ｒ謇句虚縺ｧ謖・ｮ壹＠縺ｦ縺上□縺輔＞
    pause
    exit /b 1
)

echo 笨・VOICEVOX讀懷・: %VOICEVOX_PATH%
echo.
echo CORS險ｱ蜿ｯ繝｢繝ｼ繝峨〒襍ｷ蜍穂ｸｭ...
start "" "%VOICEVOX_PATH%" --cors_policy_mode=all

timeout /t 3 > nul
echo.
echo 笨・VOICEVOX襍ｷ蜍募ｮ御ｺ・echo 繝悶Λ繧ｦ繧ｶ繧貞・隱ｭ縺ｿ霎ｼ縺ｿ縺励※髻ｳ螢ｰ騾夂衍繧偵ユ繧ｹ繝医＠縺ｦ縺上□縺輔＞
pause
