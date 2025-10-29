#!/usr/bin/env python3
"""
GitHub APIでIssueタイトルを変更してタイトル検知機能をテスト
"""
import os
import requests
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env_private", override=True)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO", "Tenormusica2024/Private")

def change_issue_title():
    """Issueタイトルを変更"""
    
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    url = f"https://api.github.com/repos/{GITHUB_REPO}/issues/1"
    
    # タイトルに「ss」を含める
    new_title = "ss remote working test4"
    
    data = {
        "title": new_title
    }
    
    try:
        print(f"Changing title to: '{new_title}'")
        response = requests.patch(url, headers=headers, json=data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Title changed successfully!")
            print(f"New title: '{result.get('title')}'")
            print(f"Updated at: {result.get('updated_at')}")
            return True
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

if __name__ == "__main__":
    change_issue_title()