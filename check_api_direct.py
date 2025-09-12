#!/usr/bin/env python3
"""
Direct GitHub API check - no filtering
"""

import os, requests
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env", override=True)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO", "Tenormusica2024/web-remote-desktop")

def check_api_direct():
    """直接APIをチェック"""
    
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    
    # Issue #1のコメント一覧を取得（最新5件のみ）
    url = f"https://api.github.com/repos/{GITHUB_REPO}/issues/1/comments"
    
    try:
        print(f"Checking: {url}")
        response = session.get(url, params={"per_page": 5, "sort": "created", "direction": "desc"})
        
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            comments = response.json()
            
            print(f"\nLatest {len(comments)} comments:")
            print("-" * 50)
            
            for i, comment in enumerate(comments):
                comment_id = comment["id"]
                author = comment["user"]["login"]
                body = comment["body"][:50] + ("..." if len(comment["body"]) > 50 else "")
                created_at = comment["created_at"]
                
                print(f"{i+1}. ID: {comment_id}")
                print(f"   Author: {author}")
                print(f"   Date: {created_at}")
                print(f"   Body: {body}")
                print()
                
            return True
            
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    check_api_direct()