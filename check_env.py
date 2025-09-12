#!/usr/bin/env python3
"""
Environment Variable Check Script
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 現在の作業ディレクトリを確認
print(f"Current working directory: {os.getcwd()}")

# .envファイルの存在確認
env_file = Path(".env")
print(f".env file exists: {env_file.exists()}")
print(f".env file path: {env_file.absolute()}")

if env_file.exists():
    print(f"\n.env file contents:")
    with open(env_file, 'r', encoding='utf-8') as f:
        content = f.read()
        print(content)
        
    # .envファイルを明示的に読み込み
    load_dotenv(".env", override=True)
    
    token = os.getenv("GITHUB_TOKEN")
    if token:
        print(f"\nLoaded token: {token[:30]}...{token[-10:]}")
        print(f"Token length: {len(token)}")
        print(f"Token starts with: {token[:20]}")
    else:
        print("\nNo token loaded from .env")

# 環境変数の直接確認
print(f"\nAll environment variables containing 'GITHUB':")
for key, value in os.environ.items():
    if 'GITHUB' in key:
        print(f"  {key}: {value[:20]}..." if len(value) > 20 else f"  {key}: {value}")