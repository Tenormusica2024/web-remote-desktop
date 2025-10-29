#!/usr/bin/env python3
"""
Alternative API endpoints to check issue title
"""
import os
import requests
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env_private", override=True)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO", "Tenormusica2024/Private")

def check_alternative_apis():
    """複数のAPIエンドポイントでIssueタイトルを確認"""
    
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    # Method 1: 通常のissues endpoint
    print("=== Method 1: Direct issue endpoint ===")
    url1 = f"https://api.github.com/repos/{GITHUB_REPO}/issues/1"
    try:
        response1 = requests.get(url1, headers=headers)
        if response1.status_code == 200:
            data1 = response1.json()
            print(f"Title: '{data1.get('title', '')}'")
        else:
            print(f"Error: {response1.status_code}")
    except Exception as e:
        print(f"Exception: {e}")
    
    # Method 2: Repository issues list (filtered)
    print("\n=== Method 2: Issues list endpoint ===")
    url2 = f"https://api.github.com/repos/{GITHUB_REPO}/issues"
    try:
        response2 = requests.get(url2, headers=headers, params={"state": "all"})
        if response2.status_code == 200:
            issues = response2.json()
            for issue in issues:
                if issue.get("number") == 1:
                    print(f"Title: '{issue.get('title', '')}'")
                    break
        else:
            print(f"Error: {response2.status_code}")
    except Exception as e:
        print(f"Exception: {e}")
    
    # Method 3: Repository events (recent activity)
    print("\n=== Method 3: Repository events ===")
    url3 = f"https://api.github.com/repos/{GITHUB_REPO}/events"
    try:
        response3 = requests.get(url3, headers=headers)
        if response3.status_code == 200:
            events = response3.json()
            for event in events[:10]:  # Check last 10 events
                if (event.get("type") == "IssuesEvent" and 
                    event.get("payload", {}).get("issue", {}).get("number") == 1):
                    issue_title = event.get("payload", {}).get("issue", {}).get("title", "")
                    print(f"Event: {event.get('payload', {}).get('action', '')} - Title: '{issue_title}'")
        else:
            print(f"Error: {response3.status_code}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    check_alternative_apis()