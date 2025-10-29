#!/usr/bin/env python3
"""
Simple screenshot posting (ASCII only)
"""
import os
import requests
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env_private", override=True)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO", "Tenormusica2024/Private")

def post_screenshot():
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }
    
    url = f"https://api.github.com/repos/{GITHUB_REPO}/issues/1/comments"
    
    screenshot_url = "https://github.com/Tenormusica2024/Private/blob/main/screenshots/2025/09/20250917_220306_AK_remote.png"
    
    body = f"""Screenshot taken (title change: "ss remote working test4")

File: {screenshot_url}
Time: 2025-09-17 22:03:06
Host: AK

![screenshot]({screenshot_url}?raw=1)

Auto-captured in response to title change detection"""

    try:
        print("Posting screenshot for title change...")
        response = requests.post(url, headers=headers, json={"body": body})
        
        if response.status_code in (200, 201):
            result = response.json()
            print("SUCCESS: Screenshot comment posted!")
            print(f"Comment ID: {result.get('id')}")
            print(f"URL: {result.get('html_url')}")
            return True
        else:
            print(f"ERROR: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"EXCEPTION: {e}")
        return False

if __name__ == "__main__":
    success = post_screenshot()
    print(f"Result: {'SUCCESS' if success else 'FAILED'}")