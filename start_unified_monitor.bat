@echo off
REM 統合版モニター起動スクリプト
REM 全機能を1つのスクリプトで実行

cd /d "%~dp0"
echo ========================================
echo 統合版GitHub Issueモニター
echo ========================================
echo.
echo 起動オプション:
echo 1. Private リポジトリのみ (デフォルト)
echo 2. Public (web-remote-desktop) のみ  
echo 3. 両方同時監視
echo 4. 1回だけ実行してテスト
echo.
echo Ctrl+Cで停止
echo.
echo ========================================
echo.

REM デフォルト: Privateリポジトリ監視
python unified_monitor.py --private --interval 5

pause