#!/usr/bin/env python3
"""
GitHub APIキャッシュをバイパスして最新のIssueタイトルを取得
"""
import os
import requests
import time
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env_private", override=True)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO", "Tenormusica2024/Private")

def force_fresh_title_check():
    """キャッシュバイパスでIssueタイトルを確認"""
    
    # 複数の方法でキャッシュをバイパス
    current_time = int(time.time())
    
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0",
        "User-Agent": f"claude-code-cache-bypass/{current_time}"
    }
    
    url = f"https://api.github.com/repos/{GITHUB_REPO}/issues/1"
    
    try:
        print("=== Force Fresh Title Check ===")
        print(f"Repository: {GITHUB_REPO}")
        print(f"Timestamp: {current_time}")
        print(f"URL: {url}")
        
        # キャッシュバスティングパラメータ付きでリクエスト
        params = {
            "t": current_time,
            "_": current_time
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            title = data.get("title", "")
            updated_at = data.get("updated_at", "")
            
            print(f"Status: {response.status_code}")
            print(f"Title: '{title}'")
            print(f"Updated: {updated_at}")
            print(f"Contains 'ss': {'ss' in title.lower()}")
            
            # ETagとLast-Modifiedを確認
            etag = response.headers.get("ETag", "N/A")
            last_modified = response.headers.get("Last-Modified", "N/A")
            cache_control = response.headers.get("Cache-Control", "N/A")
            
            print(f"\n=== Cache Headers ===")
            print(f"ETag: {etag}")
            print(f"Last-Modified: {last_modified}")
            print(f"Cache-Control: {cache_control}")
            
            return title
            
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"Exception: {e}")
        return None

def trigger_title_based_screenshot(title):
    """タイトルベースでスクリーンショットをトリガー"""
    if "ss" in title.lower():
        print(f"\n*** TITLE CONTAINS 'ss' - SHOULD TRIGGER SCREENSHOT ***")
        print(f"Title: '{title}'")
        return True
    else:
        print(f"\n*** TITLE DOES NOT CONTAIN 'ss' - NO TRIGGER ***")
        print(f"Title: '{title}'")
        return False

if __name__ == "__main__":
    fresh_title = force_fresh_title_check()
    if fresh_title:
        trigger_title_based_screenshot(fresh_title)