#!/usr/bin/env python3
"""
Force fresh GitHub API data by bypassing cache
"""
import os
import time
import requests
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env_private", override=True)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO", "Tenormusica2024/Private")

def get_fresh_issue_data():
    """強制的に最新のIssueデータを取得"""
    
    url = f"https://api.github.com/repos/{GITHUB_REPO}/issues/1"
    
    # Cache bypassing headers
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": f"claude-code-fresh-{int(time.time())}",  # Unique user agent
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache", 
        "Expires": "0",
        "If-None-Match": "",  # Force no ETag matching
        "X-Request-ID": f"force-{int(time.time())}"  # Unique request ID
    }
    
    try:
        print(f"Requesting fresh data from: {url}")
        print(f"Using timestamp: {int(time.time())}")
        
        response = requests.get(url, headers=headers, timeout=30)
        
        print(f"Status: {response.status_code}")
        print(f"Date header: {response.headers.get('Date')}")
        print(f"Last-Modified: {response.headers.get('Last-Modified')}")
        print(f"ETag: {response.headers.get('ETag')}")
        
        if response.status_code == 200:
            data = response.json()
            title = data.get("title", "")
            updated_at = data.get("updated_at", "")
            
            print(f"Title: '{title}'")
            print(f"Updated: {updated_at}")
            print(f"Contains 'ss': {'ss' in title.lower()}")
            
            return data
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"Exception: {e}")
        return None

if __name__ == "__main__":
    get_fresh_issue_data()