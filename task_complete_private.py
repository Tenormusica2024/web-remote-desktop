#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
タスク完了報告 - GitHub Issue自動投稿スクリプト (PRIVATE REPOSITORY VERSION)
Claude Codeの作業完了をGitHub Issue #1に自動報告
Private repository support with enhanced authentication
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
except:
    pass

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "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")
GITHUB_REPO = os.getenv("GITHUB_REPO", "Tenormusica2024/Private")
MONITOR_ISSUE = os.getenv("MONITOR_ISSUE_NUMBER", "1")

API_BASE = "https://api.github.com"

def post_completion_comment(custom_message=None):
    """
    GitHub Issue #1にタスク報告コメントを投稿
    
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
            # 改行を保持しながらマークダウン形式に変換
            # \nは\n\nに変換（GitHub Markdownの段落区切り）
            formatted_message = custom_message.replace("\n", "\n\n")
            
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
            print(f"OK Task report posted to GitHub Issue #1")
            print(f"Comment URL: {comment_data.get('html_url', 'N/A')}")
            print(f"Posted at: {timestamp}")
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
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    print("=" * 50)
    print("Claude Code Task Report System")
    print("=" * 50)
    
    # Command line arguments for custom message
    if len(sys.argv) > 1:
        custom_message = " ".join(sys.argv[1:])
        print(f"Custom message: {custom_message[:100]}...")  # 最初の100文字のみ表示
    else:
        custom_message = None
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
    
    print("=" * 50)

if __name__ == "__main__":
    main()