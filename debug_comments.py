#!/usr/bin/env python3
"""
Debug current comments to see what's being received
"""
import os
import requests
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env_private", override=True)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO", "Tenormusica2024/Private")

def debug_comments():
    """最新のコメントをデバッグ"""
    
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "Cache-Control": "no-cache"
    }
    
    url = f"https://api.github.com/repos/{GITHUB_REPO}/issues/1/comments"
    
    try:
        response = requests.get(url, headers=headers, params={"per_page": 10, "sort": "created", "direction": "desc"})
        
        if response.status_code == 200:
            comments = response.json()
            
            print(f"=== Latest 10 Comments ===")
            for i, comment in enumerate(comments):
                comment_id = comment["id"]
                author = comment["user"]["login"]
                body = comment["body"].strip()
                created_at = comment["created_at"]
                
                print(f"\n[{i+1}] ID: {comment_id}")
                print(f"Author: {author}")
                print(f"Created: {created_at}")
                print(f"Body: '{body}'")
                print(f"Body (lower): '{body.lower()}'")
                print(f"Is exactly 'ss': {body.lower() == 'ss'}")
                print(f"Contains 'ss': {'ss' in body.lower()}")
                print(f"Starts with 'screenshot taken': {body.lower().startswith('screenshot taken')}")
                print(f"Contains 'generated with claude code': {'generated with claude code' in body.lower()}")
                
                # Check if this would match our detection logic
                if (body.lower() == "ss" and 
                    not body.lower().startswith("screenshot taken") and
                    "generated with claude code" not in body.lower() and
                    "auto-captured in response" not in body.lower()):
                    print(">>> SHOULD TRIGGER SCREENSHOT <<<")
                else:
                    print(">>> WILL NOT TRIGGER SCREENSHOT <<<")
                    
        else:
            print(f"Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    debug_comments()