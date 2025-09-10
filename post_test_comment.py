#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test comment posting to Issue #3
"""

import requests
import os

def post_test_comment():
    """Post a test comment to Issue #3"""
    
    # GitHub settings
    token = "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"
    repo = "Tenormusica2024/web-remote-desktop"
    issue = "3"
    
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    
    owner, repo_name = repo.split("/", 1)
    url = f"https://api.github.com/repos/{owner}/{repo_name}/issues/{issue}/comments"
    
    # Test comment
    comment_body = """lower: システムテストです

これはGitHub Issue to Claude Codeシステムのテストコメントです。
このメッセージが下部ペインに表示されれば成功です。

テスト時刻: $(date)"""
    
    payload = {
        "body": comment_body
    }
    
    try:
        print(f"Posting test comment to Issue #{issue}...")
        r = session.post(url, json=payload, timeout=30)
        
        if r.status_code in [200, 201]:
            comment_data = r.json()
            print("OK Test comment posted successfully!")
            print(f"   Comment ID: {comment_data['id']}")
            print(f"   Comment URL: {comment_data['html_url']}")
            
            print("\nNext steps:")
            print("1. Run: python gh_issue_to_claude_paste.py --calibrate")
            print("2. Run: python gh_issue_to_claude_paste.py")
            print("3. The comment should appear in Claude Code lower pane")
            
            return True
        else:
            print(f"NG Comment posting failed: {r.status_code}")
            print(f"   Response: {r.text[:200]}")
            return False
            
    except Exception as e:
        print(f"NG Error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("  Posting Test Comment to Issue #3")
    print("=" * 50)
    post_test_comment()