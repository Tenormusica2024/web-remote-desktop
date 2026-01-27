#!/usr/bin/env python3
"""
GitHub Token Debug Script
トークンの詳細なデバッグを行う
"""

import os, requests, json
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
# Load private repository configuration first
load_dotenv(ROOT / ".env_private", override=True)
# Fallback to standard .env if private config not found
if not os.getenv("GITHUB_TOKEN"):
    load_dotenv(ROOT / ".env", override=True)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO", "Tenormusica2024/Private")

def debug_token():
    """トークンの詳細デバッグ"""
    
    print("=== GitHub Token Debug ===")
    print(f"Token length: {len(GITHUB_TOKEN) if GITHUB_TOKEN else 0}")
    print(f"Token prefix: {GITHUB_TOKEN[:20] if GITHUB_TOKEN else 'NOT SET'}...")
    print(f"Token suffix: ...{GITHUB_TOKEN[-10:] if GITHUB_TOKEN else 'NOT SET'}")
    print(f"Repository: {GITHUB_REPO}")
    
    if not GITHUB_TOKEN:
        print("[ERROR] GITHUB_TOKEN not set")
        return False
    
    # リクエストヘッダーの詳細表示
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "GitHub-Remote-Desktop/1.0"
    }
    
    print(f"\nRequest headers:")
    for key, value in headers.items():
        if key == "Authorization":
            print(f"  {key}: Bearer ***{value[-10:]}")
        else:
            print(f"  {key}: {value}")
    
    session = requests.Session()
    session.headers.update(headers)
    
    # 1. GitHub API のrate limit情報を取得（認証不要）
    print(f"\n1. Testing GitHub API connectivity...")
    try:
        response = session.get("https://api.github.com/rate_limit")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            rate_data = response.json()
            print(f"   Rate limit: {rate_data['rate']['remaining']}/{rate_data['rate']['limit']}")
            print(f"   [OK] GitHub API is accessible")
        else:
            print(f"   [ERROR] GitHub API connectivity issue: {response.text}")
    except Exception as e:
        print(f"   [ERROR] Connection error: {e}")
        return False
    
    # 2. 認証テスト（複数の方法を試行）
    print(f"\n2. Testing authentication methods...")
    
    # Bearer token方式
    print(f"   2.1 Bearer token authentication...")
    try:
        response = session.get("https://api.github.com/user")
        print(f"       Status: {response.status_code}")
        if response.status_code == 200:
            user_data = response.json()
            print(f"       [OK] Authenticated as: {user_data.get('login')}")
            print(f"       User ID: {user_data.get('id')}")
            print(f"       User type: {user_data.get('type')}")
            return True
        else:
            print(f"       [ERROR] Bearer auth failed: {response.text}")
    except Exception as e:
        print(f"       [ERROR] Bearer auth error: {e}")
    
    # token parameter方式（Classic tokenの場合）
    print(f"   2.2 Token parameter authentication...")
    try:
        response = requests.get(f"https://api.github.com/user?access_token={GITHUB_TOKEN}")
        print(f"       Status: {response.status_code}")
        if response.status_code == 200:
            user_data = response.json()
            print(f"       [OK] Authenticated as: {user_data.get('login')}")
            return True
        else:
            print(f"       [ERROR] Token param auth failed: {response.text}")
    except Exception as e:
        print(f"       [ERROR] Token param auth error: {e}")
    
    # Basic auth方式
    print(f"   2.3 Basic authentication...")
    try:
        response = requests.get("https://api.github.com/user", 
                              auth=(GITHUB_TOKEN, 'x-oauth-basic'))
        print(f"       Status: {response.status_code}")
        if response.status_code == 200:
            user_data = response.json()
            print(f"       [OK] Authenticated as: {user_data.get('login')}")
            return True
        else:
            print(f"       [ERROR] Basic auth failed: {response.text}")
    except Exception as e:
        print(f"       [ERROR] Basic auth error: {e}")
    
    print(f"\n=== Debug Summary ===")
    print(f"All authentication methods failed.")
    print(f"Possible issues:")
    print(f"1. Token is invalid or expired")
    print(f"2. Token lacks 'user' scope")
    print(f"3. Token format is incorrect")
    print(f"4. Network connectivity issues")
    
    return False

if __name__ == "__main__":
    debug_token()