#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Screenshot Command Sender (for Office PC)
社内PCからGitHub Issue経由で自宅PCにスクリーンショット指示を送信
"""

import os, sys, argparse
import requests
from datetime import datetime

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = lambda *a, **k: None

# ---------- Config ----------
# 社内PC用設定（.env または環境変数から読み込み）
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()
GITHUB_REPO = os.getenv("GITHUB_REPO", "").strip()  # "owner/repo"
MONITOR_ISSUE = os.getenv("MONITOR_ISSUE_NUMBER", "1").strip()

API_BASE = "https://api.github.com"

def send_screenshot_command(message="screenshot", note=""):
    """スクリーンショット指示を GitHub Issue に送信"""
    
    if not GITHUB_TOKEN or not GITHUB_REPO:
        print("ERROR: GITHUB_TOKEN と GITHUB_REPO を環境変数または .env に設定してください")
        sys.exit(1)
    
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    
    owner, repo = GITHUB_REPO.split("/", 1)
    url = f"{API_BASE}/repos/{owner}/{repo}/issues/{MONITOR_ISSUE}/comments"
    
    # コメント本文を作成
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    body_parts = [
        f"🔍 **Remote Screenshot Request**",
        f"⏰ **Time**: {timestamp}",
        f"💻 **From**: Office PC"
    ]
    
    if note:
        body_parts.append(f"📝 **Note**: {note}")
    
    body_parts.append(f"\n{message}")
    
    body = "\n".join(body_parts)
    
    try:
        print(f"Sending screenshot command to Issue #{MONITOR_ISSUE}...")
        print(f"Repository: {GITHUB_REPO}")
        
        r = session.post(url, json={"body": body}, timeout=30)
        
        if r.status_code in (200, 201):
            response_data = r.json()
            comment_url = response_data.get("html_url", "")
            print("✅ Screenshot command sent successfully!")
            print(f"Comment URL: {comment_url}")
            print(f"自宅PCが監視中であれば、30秒以内にスクリーンショットが撮影されます。")
        else:
            print(f"❌ Failed to send command: {r.status_code}")
            print(f"Response: {r.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    parser = argparse.ArgumentParser(description="Send remote screenshot command via GitHub Issue")
    parser.add_argument("--message", "-m", default="screenshot", help="Command message (default: 'screenshot')")
    parser.add_argument("--note", "-n", default="", help="Optional note to include")
    parser.add_argument("--urgent", "-u", action="store_true", help="Mark as urgent (adds 🚨)")
    args = parser.parse_args()
    
    message = args.message
    if args.urgent:
        message = f"🚨 URGENT: {message}"
    
    send_screenshot_command(message, args.note)

if __name__ == "__main__":
    main()