#!/usr/bin/env python3
"""
Private repository Issue状況確認
"""
import os
import requests
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env_private", override=True)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO", "Tenormusica2024/Private")

def check_current_status():
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }
    
    # Issue情報を取得
    url = f"https://api.github.com/repos/{GITHUB_REPO}/issues/1"
    
    try:
        print(f"Checking Private repository: {GITHUB_REPO}")
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            issue_data = response.json()
            current_title = issue_data.get("title", "")
            updated_at = issue_data.get("updated_at", "")
            
            print(f"Current title: '{current_title}'")
            print(f"Last updated: {updated_at}")
            
            # 最新コメント確認
            comments_url = f"https://api.github.com/repos/{GITHUB_REPO}/issues/1/comments"
            comments_response = requests.get(comments_url, headers=headers, params={"per_page": 3})
            
            if comments_response.status_code == 200:
                comments = comments_response.json()
                print(f"\nLatest {len(comments)} comments:")
                
                for i, comment in enumerate(comments[-3:]):
                    author = comment["user"]["login"]
                    body = comment["body"]
                    created_at = comment["created_at"]
                    
                    print(f"  [{i+1}] {created_at} - {author}")
                    if "screenshot" in body.lower():
                        print(f"      📸 Screenshot comment found!")
                        if "![screenshot]" in body:
                            print(f"      ✅ Image embedded")
                        else:
                            print(f"      ❌ No image embedded")
                    print(f"      Preview: {body[:100]}...")
            
            return True
        else:
            print(f"ERROR: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"EXCEPTION: {e}")
        return False

def test_new_title():
    """新しいタイトルでテスト"""
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }
    
    url = f"https://api.github.com/repos/{GITHUB_REPO}/issues/1"
    
    timestamp = datetime.now().strftime("%H%M%S")
    new_title = f"ss new test {timestamp}"
    
    data = {"title": new_title}
    
    try:
        print(f"\nChanging title to: '{new_title}'")
        response = requests.patch(url, headers=headers, json=data)
        
        if response.status_code == 200:
            print("✅ Title changed successfully!")
            print("Monitor should detect this change...")
            return True
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

if __name__ == "__main__":
    print("=== Private Repository Status Check ===")
    check_current_status()
    
    print("\n" + "="*50)
    print("Testing new title change...")
    test_new_title()