#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Private Repository API Access Test - Minimal Configuration
privateリポジトリのAPI読み取りアクセステスト用最小構成スクリプト
"""

import requests
import os
import json
from pathlib import Path
from datetime import datetime

def load_env():
    """Environment variables loading - Private priority"""
    env_private = Path(__file__).parent / ".env_private"
    env_default = Path(__file__).parent / ".env"
    
    # .env_privateが存在すれば優先使用
    env_file = env_private if env_private.exists() else env_default
    
    if env_file.exists():
        print(f"Loading config from: {env_file}")
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
    else:
        print("No environment file found")

def test_private_api_access():
    """Private Repository API アクセステスト"""
    load_env()
    
    # Configuration
    github_token = os.getenv("GITHUB_TOKEN")
    github_repo = os.getenv("GITHUB_REPO", "Tenormusica2024/Private")
    issue_number = os.getenv("GH_ISSUE", "1")
    
    print("=" * 60)
    print("Private Repository API Access Test")
    print("=" * 60)
    print(f"Repository: {github_repo}")
    print(f"Issue: #{issue_number}")
    print(f"Token: {github_token[:20]}..." if github_token else "No token")
    print()
    
    if not github_token:
        print("❌ GITHUB_TOKEN not found")
        return False
    
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "minimal-private-api-test/1.0"
    }
    
    try:
        owner, repo = github_repo.split("/", 1)
        
        # Test 1: Repository information
        print("[Test 1] Repository access...")
        repo_url = f"https://api.github.com/repos/{owner}/{repo}"
        response = requests.get(repo_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            repo_data = response.json()
            print("[OK] Repository access: PASS")
            print(f"   Repository: {repo_data.get('full_name')}")
            print(f"   Private: {repo_data.get('private')}")
            print(f"   Permissions: {repo_data.get('permissions', {})}")
        else:
            print(f"[NG] Repository access failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
        
        print()
        
        # Test 2: Issue access
        print("[Test 2] Issue access...")
        issue_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}"
        response = requests.get(issue_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            issue_data = response.json()
            print("[OK] Issue access: PASS")
            print(f"   Title: {issue_data.get('title')}")
            print(f"   State: {issue_data.get('state')}")
            print(f"   Comments: {issue_data.get('comments')}")
        else:
            print(f"[NG] Issue access failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
        
        print()
        
        # Test 3: Comments access
        print("[Test 3] Comments access...")
        comments_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments"
        response = requests.get(comments_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            comments_data = response.json()
            print("[OK] Comments access: PASS")
            print(f"   Total comments: {len(comments_data)}")
            
            if comments_data:
                latest = comments_data[-1]
                print(f"   Latest comment:")
                print(f"     ID: {latest.get('id')}")
                print(f"     Author: {latest.get('user', {}).get('login')}")
                print(f"     Created: {latest.get('created_at')}")
                print(f"     Body: {latest.get('body', '')[:100]}...")
            else:
                print("   No comments found")
                
        else:
            print(f"[NG] Comments access failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
        
        print()
        print("[SUCCESS] All API tests passed - Private repository access working")
        return True
        
    except Exception as e:
        print(f"[ERROR] Exception occurred: {e}")
        return False

def main():
    """Main execution"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"Execution time: {timestamp}")
    print()
    
    success = test_private_api_access()
    
    print()
    print("=" * 60)
    if success:
        print("[SUCCESS] Private Repository API Access: WORKING")
        print("Ready to implement comment monitoring script")
    else:
        print("[FAILED] Private Repository API Access: FAILED")
        print("Please check token permissions and repository access")
    print("=" * 60)

if __name__ == "__main__":
    main()