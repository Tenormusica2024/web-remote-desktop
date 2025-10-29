#!/usr/bin/env python3
"""
GitHub Repository Private Converter
Different token types and authentication methods
"""
import requests
import os
from pathlib import Path

# Configuration
ROOT = Path(__file__).resolve().parent
GITHUB_REPO = "Tenormusica2024/web-remote-desktop"

# Try multiple token approaches
TOKENS = [
    # Current token
    "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",
    # Try alternative header approaches
]

def test_token_permissions(token):
    """Test what permissions a token has"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    # Test repository access
    url = f"https://api.github.com/repos/{GITHUB_REPO}"
    response = requests.get(url, headers=headers)
    
    print(f"Repository access: {response.status_code}")
    if response.status_code == 200:
        repo_data = response.json()
        print(f"Current visibility: {'Private' if repo_data.get('private') else 'Public'}")
        print(f"Permissions: {repo_data.get('permissions', {})}")
        return True
    else:
        print(f"Access denied: {response.text}")
        return False

def try_different_auth_methods(token):
    """Try different authentication methods"""
    methods = [
        {
            "name": "Bearer Token",
            "headers": {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28"
            }
        },
        {
            "name": "Token Auth",
            "headers": {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github+json"
            }
        },
        {
            "name": "Basic Auth with Token",
            "auth": ("Tenormusica2024", token),
            "headers": {
                "Accept": "application/vnd.github+json"
            }
        }
    ]
    
    for method in methods:
        print(f"\nTrying: {method['name']}")
        
        # Prepare request
        kwargs = {"headers": method["headers"]}
        if "auth" in method:
            kwargs["auth"] = method["auth"]
            
        url = f"https://api.github.com/repos/{GITHUB_REPO}"
        
        # Test GET first
        response = requests.get(url, **kwargs)
        print(f"GET Status: {response.status_code}")
        
        if response.status_code == 200:
            # Try PATCH to make private
            patch_data = {"private": True}
            patch_response = requests.patch(url, json=patch_data, **kwargs)
            print(f"PATCH Status: {patch_response.status_code}")
            
            if patch_response.status_code in (200, 201):
                print("SUCCESS: Repository made private!")
                return True
            else:
                print(f"PATCH Failed: {patch_response.text}")
        else:
            print(f"GET Failed: {response.text}")
    
    return False

def main():
    print("GitHub Repository Private Converter")
    print("=" * 50)
    
    token = TOKENS[0]
    
    print("Step 1: Testing token permissions...")
    if not test_token_permissions(token):
        print("Token has insufficient permissions")
        return False
    
    print("\nStep 2: Trying different authentication methods...")
    success = try_different_auth_methods(token)
    
    if success:
        print("\n✅ Repository successfully made private!")
    else:
        print("\n❌ All methods failed. Manual conversion required.")
        print("\nManual steps:")
        print("1. Go to https://github.com/Tenormusica2024/web-remote-desktop/settings")
        print("2. Scroll down to 'Danger Zone'")
        print("3. Click 'Change repository visibility'")
        print("4. Select 'Make private'")
    
    return success

if __name__ == "__main__":
    main()