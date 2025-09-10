@echo off
echo =================================
echo  Claude Code Remote Setup
echo =================================
echo.
echo このスクリプトは、GitHub Issue to Claude Code システムの環境変数を設定します。
echo.

REM 既存のスクリーンショットシステムと同じGitHub設定を使用
set GH_REPO=Tenormusica2024/web-remote-desktop
set GH_ISSUE=3
set GH_TOKEN=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

REM オプション設定
set POLL_SEC=5
set DEFAULT_PANE=lower
set ONLY_AUTHOR=Tenormusica2024

echo 設定内容:
echo   GitHub Repository: %GH_REPO%
echo   監視Issue番号: %GH_ISSUE%
echo   ポーリング間隔: %POLL_SEC% 秒
echo   デフォルトペイン: %GH_PANE%
echo   処理対象ユーザー: %ONLY_AUTHOR%
echo.

echo 必要な依存関係をインストールしています...
pip install requests pyautogui pyperclip pillow
echo.

echo 設定完了！
echo.
echo 使い方:
echo   1. キャリブレーション（初回のみ）: python gh_issue_to_claude_paste.py --calibrate
echo   2. システム開始: python gh_issue_to_claude_paste.py
echo.
echo GitHub Issue #%GH_ISSUE% にコメントを投稿すると、Claude Codeに自動送信されます。
echo.
echo コメント例:
echo   upper: これを右上に送って
echo   lower: これは右下に送って
echo   プレフィックスなし（%DEFAULT_PANE%に送信）
echo.
pause