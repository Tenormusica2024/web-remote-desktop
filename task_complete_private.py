#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
タスク完了報告 - GitHub Issue自動投稿スクリプト (PRIVATE REPOSITORY VERSION)
Claude Codeの作業完了をGitHub Issueに自動報告
Private repository support with enhanced authentication
v4: セキュリティ強化、UTF8NoBOM対応、Issue番号動的化
"""

import requests
import sys
from datetime import datetime
import os
from pathlib import Path

# 設定 - Private Repository Version
ROOT = Path(__file__).resolve().parent
try:
    from dotenv import load_dotenv
    # Load private repository configuration first
    load_dotenv(ROOT / ".env_private", override=True)
    # Fallback to standard .env if private config not found
    if not os.getenv("GITHUB_TOKEN"):
        load_dotenv(ROOT / ".env", override=True)
except ImportError:
    # python-dotenv not installed - rely on environment variables
    pass
except Exception as e:
    # .env file loading failed - rely on environment variables
    print(f"Warning: Failed to load .env file: {e}", file=sys.stderr)

# トークンは環境変数または.envファイルから取得（ハードコード禁止）
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    print("ERROR: GITHUB_TOKEN not found in environment or .env file")
    print("Please set GITHUB_TOKEN in .env_private or .env file")
    sys.exit(1)
GITHUB_REPO = os.getenv("GITHUB_REPO", "Tenormusica2024/Private")
MONITOR_ISSUE = os.getenv("MONITOR_ISSUE_NUMBER", "5")

API_BASE = "https://api.github.com"

# 最終報告時刻を記録するファイル（Session Endフックとの連携用）
LAST_REPORT_FILE = ROOT / ".last_report_timestamp"

def post_completion_comment(custom_message=None):
    """
    GitHub Issue（MONITOR_ISSUE番号）にタスク報告コメントを投稿

    システムプロンプト:
    - 必ずマークダウン形式で投稿する
    - タスク完了時だけでなく、終了時・停止時・待機時・エラー時も報告する
    - カスタムメッセージは改行を保持し、マークダウン形式で整形する
    - 見出し、リスト、コードブロックなどのマークダウン記法を正しく処理する
    """
    try:
        owner, repo = GITHUB_REPO.split("/", 1)
        url = f"{API_BASE}/repos/{owner}/{repo}/issues/{MONITOR_ISSUE}/comments"
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if custom_message:
            # メッセージをそのまま使用（改行の二重化はコードブロックを壊すため削除）
            # GitHub Markdownは元の改行を適切に処理する
            formatted_message = custom_message

            # マークダウン形式で整形された報告を作成
            body = f"""## 🤖 タスク報告

{formatted_message}

---

⏰ **報告時刻**: {timestamp}  
💻 **実行者**: Claude Code"""
        else:
            body = f"""## 🤖 タスク報告

⏰ **報告時刻**: {timestamp}  
💻 **実行者**: Claude Code"""
        
        headers = {
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "claude-code-private-task-complete/1.0"
        }
        
        response = requests.post(url, json={"body": body}, headers=headers, timeout=30)
        
        if response.status_code in (200, 201):
            comment_data = response.json()
            print(f"OK Task report posted to GitHub Issue #{MONITOR_ISSUE}")
            print(f"Comment URL: {comment_data.get('html_url', 'N/A')}")
            print(f"Posted at: {timestamp}")
            
            # 最終報告時刻を記録（Session Endフックが重複報告を防ぐため）
            try:
                with open(LAST_REPORT_FILE, 'w', encoding='utf-8') as f:
                    f.write(datetime.now().isoformat())
            except Exception as e:
                print(f"Warning: Failed to write last report timestamp: {e}")
            
            return True
        else:
            print(f"NG Post failed: {response.status_code}")
            print(f"Error details: {response.text}")
            return False
            
    except Exception as e:
        print(f"NG Error occurred: {e}")
        return False

def main():
    # UTF-8エンコーディング設定（Windows環境対応）
    import sys
    import io
    import argparse
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

    print("=" * 50)
    print("Claude Code Task Report System")
    print("=" * 50)

    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Post task report to GitHub Issue')
    parser.add_argument('message', nargs='*', help='Custom message to post')
    parser.add_argument('--file', '-f', type=str, help='Read message from file (for special characters)')
    args = parser.parse_args()

    # Determine custom message
    custom_message = None
    if args.file:
        # ファイルから読み取り（特殊文字対応）
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                custom_message = f.read()
            print(f"Custom message from file: {custom_message[:100]}...")
        except Exception as e:
            print(f"Error reading file: {e}")
            sys.exit(1)
    elif args.message:
        custom_message = " ".join(args.message)
        print(f"Custom message: {custom_message[:100]}...")
    else:
        print("Using standard report message")

    print(f"Target: {GITHUB_REPO} Issue #{MONITOR_ISSUE}")
    print(f"Execution time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Execute GitHub Issue post
    success = post_completion_comment(custom_message)

    print()
    if success:
        print("OK Task report posted successfully!")
    else:
        print("NG Task report failed.")
        sys.exit(1)

    print("=" * 50)

if __name__ == "__main__":
    main()