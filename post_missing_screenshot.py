#!/usr/bin/env python3
"""
タイトル変更時の欠落スクリーンショットを手動投稿
"""
import os
import requests
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env_private", override=True)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO", "Tenormusica2024/Private")

def post_missing_screenshot():
    """タイトル変更時のスクリーンショットを投稿"""
    
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }
    
    url = f"https://api.github.com/repos/{GITHUB_REPO}/issues/1/comments"
    
    # タイトル変更時のスクリーンショット情報
    screenshot_url = "https://github.com/Tenormusica2024/Private/blob/main/screenshots/2025/09/20250917_220306_AK_remote.png"
    timestamp = "2025-09-17 22:03:06"
    
    body = f"""✅ **Screenshot taken** (requested by title change: "ss remote working test4")

📸 **File**: {screenshot_url}
🕒 **Time**: {timestamp}  
💻 **Host**: AK

![screenshot]({screenshot_url}?raw=1)

*Auto-captured in response to title change detection*"""

    try:
        print(f"Posting missing screenshot for title change...")
        response = requests.post(url, headers=headers, json={"body": body})
        
        if response.status_code in (200, 201):
            result = response.json()
            print(f"✅ Screenshot comment posted successfully!")
            print(f"Comment ID: {result.get('id')}")
            print(f"URL: {result.get('html_url')}")
            return True
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

if __name__ == "__main__":
    post_missing_screenshot()