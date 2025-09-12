#!/usr/bin/env python3
"""
Get the latest comment ID from GitHub API
"""

import os, requests
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env", override=True)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO", "Tenormusica2024/web-remote-desktop")

def get_latest_comment_id():
    """最新のコメントIDを取得"""
    
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    
    # Issue #1の最新コメント1件を取得
    url = f"https://api.github.com/repos/{GITHUB_REPO}/issues/1/comments"
    
    try:
        response = session.get(url, params={"per_page": 1, "sort": "created", "direction": "desc"})
        
        if response.status_code == 200:
            comments = response.json()
            if comments:
                latest_id = comments[0]["id"]
                print(f"Latest comment ID: {latest_id}")
                
                # last_comment_id.txt に保存
                last_file = ROOT / "last_comment_id.txt"
                last_file.write_text(str(latest_id))
                print(f"Updated {last_file} with ID: {latest_id}")
                
                return latest_id
            else:
                print("No comments found")
                return None
            
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    get_latest_comment_id()