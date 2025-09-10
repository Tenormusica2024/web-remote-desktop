#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Issue Title Updater for Screenshot Commands
社内PCからIssueのタイトルを変更してスクリーンショット指示を送信
"""

import requests
import sys
from datetime import datetime

# 設定
GITHUB_TOKEN = "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"
GITHUB_REPO = "Tenormusica2024/web-remote-desktop"
MONITOR_ISSUE = "1"
API_BASE = "https://api.github.com"

SESSION = requests.Session()
SESSION.headers.update({
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
})

def update_issue_title(new_title):
    """Issueのタイトルを更新"""
    try:
        owner, repo = GITHUB_REPO.split("/", 1)
        url = f"{API_BASE}/repos/{owner}/{repo}/issues/{MONITOR_ISSUE}"
        
        payload = {
            "title": new_title
        }
        
        r = SESSION.patch(url, json=payload, timeout=30)
        if r.status_code == 200:
            issue_data = r.json()
            try:
                print(f"✅ Issue title updated successfully!")
                print(f"   New title: {issue_data['title']}")
                print(f"   Issue URL: {issue_data['html_url']}")
            except UnicodeEncodeError:
                # ASCII文字のみでログ出力
                print("OK Issue title updated successfully!")
                print(f"   New title: {issue_data['title']}")
                print(f"   Issue URL: {issue_data['html_url']}")
            return True
        else:
            try:
                print(f"❌ Failed to update title: {r.status_code} {r.text}")
            except UnicodeEncodeError:
                print(f"NG Failed to update title: {r.status_code} {r.text}")
            return False
            
    except Exception as e:
        try:
            print(f"❌ Error: {e}")
        except UnicodeEncodeError:
            print(f"NG Error: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python update-issue-title.py <new_title>")
        print("Examples:")
        print("  python update-issue-title.py 'ss'")
        print("  python update-issue-title.py 'ss status check'")
        print("  python update-issue-title.py 'Remote Control Commands'")
        return
    
    new_title = sys.argv[1]
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    print(f"[Office PC] Updating Issue title at {timestamp}...")
    print(f"[Office PC] New title: '{new_title}'")
    
    if update_issue_title(new_title):
        try:
            print("[Office PC] Command sent via title update!")
        except UnicodeEncodeError:
            print("[Office PC] Command sent via title update!")
    else:
        try:
            print("[Office PC] Failed to send command.")
        except UnicodeEncodeError:
            print("[Office PC] Failed to send command.")

if __name__ == "__main__":
    main()