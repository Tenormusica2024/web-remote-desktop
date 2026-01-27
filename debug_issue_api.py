#!/usr/bin/env python3
"""
GitHub Issue API Debug Tool - Private Repository Version
APIレスポンスを詳細に確認してタイトル変更の反映状況をチェック
"""
import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# Configuration
ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env_private", override=True)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO", "Tenormusica2024/Private")
ISSUE_NUMBER = "1"

def debug_issue_api():
    """Issue API の詳細デバッグ"""
    
    print(f"=== GitHub Issue API Debug ===")
    print(f"Repository: {GITHUB_REPO}")
    print(f"Issue: #{ISSUE_NUMBER}")
    print(f"Token: {GITHUB_TOKEN[:10]}..." if GITHUB_TOKEN else "No token")
    print(f"Time: {datetime.now()}")
    print()
    
    # Headers
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "claude-code-debug/1.0",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache"
    }
    
    # API URL
    url = f"https://api.github.com/repos/{GITHUB_REPO}/issues/{ISSUE_NUMBER}"
    
    print(f"Request URL: {url}")
    print(f"Headers: {dict(headers)}")
    print()
    
    try:
        # Make request
        response = requests.get(url, headers=headers, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
        print()
        
        if response.status_code == 200:
            data = response.json()
            
            # Important fields
            title = data.get("title", "")
            number = data.get("number", "")
            state = data.get("state", "")
            updated_at = data.get("updated_at", "")
            user = data.get("user", {}).get("login", "")
            
            print(f"=== ISSUE DATA ===")
            print(f"Title: '{title}'")
            print(f"Number: {number}")
            print(f"State: {state}")
            print(f"Updated: {updated_at}")
            print(f"Author: {user}")
            print()
            
            # Check for 'ss'
            title_lower = title.lower()
            contains_ss = "ss" in title_lower
            
            print(f"=== SS DETECTION ===")
            print(f"Title (lowercase): '{title_lower}'")
            print(f"Contains 'ss': {contains_ss}")
            print()
            
            if contains_ss:
                print("✅ SHOULD TRIGGER SCREENSHOT")
            else:
                print("❌ WILL NOT TRIGGER SCREENSHOT")
                
            # Show full JSON for debugging
            print(f"=== FULL JSON RESPONSE ===")
            print(json.dumps(data, indent=2))
            
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    debug_issue_api()