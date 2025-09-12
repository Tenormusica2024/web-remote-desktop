#!/usr/bin/env python3
"""
GitHub Personal Access Token Setup Script
"""

import os
from pathlib import Path

def setup_new_token():
    """新しいGitHub Personal Access Tokenの設定"""
    
    root = Path(__file__).resolve().parent
    env_file = root / ".env"
    
    print("=== GitHub Personal Access Token Setup ===")
    print("Please paste your new GitHub Personal Access Token below:")
    print("(Token should start with 'ghp_' or 'github_pat_')")
    print()
    
    new_token = input("New GitHub Token: ").strip()
    
    if not new_token:
        print("❌ No token provided. Exiting.")
        return False
    
    # Fine-grained tokenも受け入れるように更新
    valid_prefixes = ['ghp_', 'github_pat_', 'gho_', 'ghu_', 'ghs_']
    if not any(new_token.startswith(prefix) for prefix in valid_prefixes):
        print("⚠️ Warning: Token doesn't start with expected prefix")
        print("Valid prefixes: ghp_ (classic), github_pat_ (classic), gho_/ghu_/ghs_ (fine-grained)")
        confirm = input("Continue anyway? (y/N): ").strip().lower()
        if confirm != 'y':
            print("Setup cancelled.")
            return False
    
    try:
        # .envファイル更新
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # トークン行を置換
        lines = content.split('\n')
        updated_lines = []
        
        for line in lines:
            if line.startswith('GITHUB_TOKEN='):
                updated_lines.append(f'GITHUB_TOKEN={new_token}')
                print("✅ Token updated in .env file")
            else:
                updated_lines.append(line)
        
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(updated_lines))
        
        print("✅ Configuration updated successfully!")
        print()
        print("Next steps:")
        print("1. Run: python test_github_access.py")
        print("2. Run: python remote-monitor.py --test") 
        print("3. Start monitoring: python remote-monitor.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating configuration: {e}")
        return False

if __name__ == "__main__":
    setup_new_token()