#!/usr/bin/env python3
"""
Force GitHub API cache refresh by making a minimal update to the issue
"""
import os
import requests
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env_private", override=True)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO", "Tenormusica2024/Private")

def force_api_refresh():
    """Issue に軽微な更新を行ってAPIキャッシュを強制リフレッシュ"""
    
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    # まず現在のIssue情報を取得
    get_url = f"https://api.github.com/repos/{GITHUB_REPO}/issues/1"
    
    print("Getting current issue data...")
    response = requests.get(get_url, headers=headers)
    
    if response.status_code != 200:
        print(f"Error getting issue: {response.status_code}")
        return
    
    current_data = response.json()
    current_title = current_data.get("title", "")
    current_body = current_data.get("body", "")
    
    print(f"Current API title: '{current_title}'")
    
    # Issue に軽微な更新を行う（ボディに小さなスペースを追加）
    update_url = f"https://api.github.com/repos/{GITHUB_REPO}/issues/1"
    
    # 現在のボディの最後にスペースを追加して更新
    updated_body = (current_body or "").rstrip() + " "
    
    update_data = {
        "body": updated_body
    }
    
    print("Forcing API refresh by updating issue body...")
    update_response = requests.patch(update_url, json=update_data, headers=headers)
    
    if update_response.status_code == 200:
        updated_data = update_response.json()
        updated_title = updated_data.get("title", "")
        print(f"Update successful!")
        print(f"New API title: '{updated_title}'")
        print(f"Contains 'ss': {'ss' in updated_title.lower()}")
        
        if "ss" in updated_title.lower():
            print("✓ API now shows correct title with 'ss'")
        else:
            print("× API still shows old title")
            
    else:
        print(f"Update failed: {update_response.status_code} - {update_response.text}")

if __name__ == "__main__":
    force_api_refresh()