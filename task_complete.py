#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
タスク完了報告 - GitHub Issue自動投稿スクリプト
Claude Codeの作業完了をGitHub Issue #1に自動報告
"""

import requests
import sys
from datetime import datetime
import os
from pathlib import Path

# 設定
ROOT = Path(__file__).resolve().parent
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env", override=True)
except:
    pass

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "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")
GITHUB_REPO = os.getenv("GITHUB_REPO", "Tenormusica2024/web-remote-desktop")
MONITOR_ISSUE = os.getenv("MONITOR_ISSUE_NUMBER", "1")

API_BASE = "https://api.github.com"

def post_completion_comment(custom_message=None):
    """GitHub Issue #1にタスク完了コメントを投稿"""
    try:
        owner, repo = GITHUB_REPO.split("/", 1)
        url = f"{API_BASE}/repos/{owner}/{repo}/issues/{MONITOR_ISSUE}/comments"
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if custom_message:
            body = f"🤖 **タスク完了報告**\n\n{custom_message}\n\n⏰ **完了時刻**: {timestamp}\n💻 **実行者**: Claude Code"
        else:
            body = f"🤖 **タスク完了**\n\n⏰ **完了時刻**: {timestamp}\n💻 **実行者**: Claude Code"
        
        headers = {
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        
        response = requests.post(url, json={"body": body}, headers=headers, timeout=30)
        
        if response.status_code in (200, 201):
            comment_data = response.json()
            print(f"OK Task completion report posted to GitHub Issue #1")
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
    print("=" * 50)
    print("Claude Code Task Complete Report System")
    print("=" * 50)
    
    # Command line arguments for custom message
    if len(sys.argv) > 1:
        custom_message = " ".join(sys.argv[1:])
        print(f"Custom message: {custom_message}")
    else:
        custom_message = None
        print("Using standard completion message")
    
    print(f"Target: {GITHUB_REPO} Issue #{MONITOR_ISSUE}")
    print(f"Execution time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Execute GitHub Issue post
    success = post_completion_comment(custom_message)
    
    print()
    if success:
        print("OK Task completion report posted successfully!")
    else:
        print("NG Task completion report failed.")
    
    print("=" * 50)

if __name__ == "__main__":
    main()