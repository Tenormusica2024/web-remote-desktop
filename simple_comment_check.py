#!/usr/bin/env python3
"""
Simple comment checker without unicode issues
"""
import os
import requests
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env_private", override=True)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO", "Tenormusica2024/Private")

def check_latest_comments():
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }
    
    url = f"https://api.github.com/repos/{GITHUB_REPO}/issues/1/comments"
    
    try:
        response = requests.get(url, headers=headers, params={"per_page": 5, "sort": "created", "direction": "desc"})
        
        if response.status_code == 200:
            comments = response.json()
            
            print("=== Latest 5 Comments ===")
            for i, comment in enumerate(comments):
                comment_id = comment["id"]
                author = comment["user"]["login"]
                body = comment["body"][:100] + "..." if len(comment["body"]) > 100 else comment["body"]
                created_at = comment["created_at"]
                
                print(f"\n[{i+1}] ID: {comment_id}")
                print(f"Author: {author}")
                print(f"Created: {created_at}")
                print(f"Body: {body}")
                
        else:
            print(f"Error: {response.status_code}")
            
    except Exception as e:
        print(f"Exception: {str(e)}")

if __name__ == "__main__":
    check_latest_comments()