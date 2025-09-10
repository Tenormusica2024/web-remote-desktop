#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple test for remote control system
"""

import os
import requests

def setup_env():
    """Set environment variables"""
    env_vars = {
        "GH_REPO": "Tenormusica2024/web-remote-desktop",
        "GH_ISSUE": "3",
        "GH_TOKEN": "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",
        "POLL_SEC": "5",
        "DEFAULT_PANE": "lower",
        "ONLY_AUTHOR": "Tenormusica2024"
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
    
    print("OK Environment variables set")

def test_github_api():
    """Test GitHub API connection"""
    token = os.getenv("GH_TOKEN")
    repo = os.getenv("GH_REPO")
    issue = os.getenv("GH_ISSUE")
    
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    
    try:
        owner, repo_name = repo.split("/", 1)
        url = f"https://api.github.com/repos/{owner}/{repo_name}/issues/{issue}"
        
        print(f"Testing GitHub API: {url}")
        
        r = session.get(url, timeout=10)
        if r.status_code == 200:
            issue_data = r.json()
            print("OK GitHub API connection successful!")
            print(f"   Issue title: {issue_data.get('title')}")
            print(f"   Issue URL: {issue_data.get('html_url')}")
            return True
        else:
            print(f"NG GitHub API error: {r.status_code}")
            return False
            
    except Exception as e:
        print(f"NG Connection failed: {e}")
        return False

def test_dependencies():
    """Test required packages"""
    print("Testing dependencies...")
    deps = ["requests", "pyautogui", "pyperclip"]
    
    for dep in deps:
        try:
            __import__(dep)
            print(f"   OK {dep}")
        except ImportError:
            print(f"   NG {dep} - Not installed")
            return False
    
    return True

def main():
    print("=" * 50)
    print("  Remote Control System Simple Test")
    print("=" * 50)
    
    setup_env()
    
    tests_ok = 0
    
    if test_github_api():
        tests_ok += 1
    
    if test_dependencies():
        tests_ok += 1
    
    print(f"\nTest results: {tests_ok}/2 passed")
    
    if tests_ok == 2:
        print("\nOK All tests passed! Ready for calibration.")
        print("\nNext steps:")
        print("1. python gh_issue_to_claude_paste.py --calibrate")
        print("2. python gh_issue_to_claude_paste.py")
        print("3. Post comment to Issue #3")
    else:
        print("\nNG Some tests failed. Please fix issues.")

if __name__ == "__main__":
    main()