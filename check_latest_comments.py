#!/usr/bin/env python3
"""
Check latest comments on GitHub Issue
最新のコメントを確認
"""

import os, requests
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env_private", override=True)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO", "Tenormusica2024/Private")

def check_latest_comments():
    """最新コメントの確認"""
    
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    
    # Issue #1のコメント一覧を取得
    url = f"https://api.github.com/repos/{GITHUB_REPO}/issues/1/comments"
    
    try:
        response = session.get(url, params={"per_page": 20, "sort": "created", "direction": "desc"})
        
        if response.status_code == 200:
            comments = response.json()
            
            print(f"Latest {len(comments)} comments on Issue #1:")
            print("-" * 60)
            
            # last_comment_id_private.txtの内容を読み取り
            last_id_file = ROOT / "last_comment_id_private.txt"
            last_processed_id = 0
            if last_id_file.exists():
                try:
                    last_processed_id = int(last_id_file.read_text().strip())
                    print(f"Last processed comment ID: {last_processed_id}")
                    print("-" * 60)
                except:
                    pass
            
            for i, comment in enumerate(reversed(comments)):  # 古い順に表示
                comment_id = comment["id"]
                author = comment["user"]["login"]
                body = comment["body"][:100] + ("..." if len(comment["body"]) > 100 else "")
                created_at = comment["created_at"]
                
                status = ""
                if comment_id <= last_processed_id:
                    status = "[PROCESSED]"
                else:
                    status = "[NEW]"
                
                print(f"{i+1:2d}. ID: {comment_id} {status}")
                print(f"    Author: {author}")
                print(f"    Date: {created_at}")
                print(f"    Body: {body}")
                
                # 新しいコメントで「ss」のみのものをチェック
                if (comment_id > last_processed_id and 
                    body.lower().strip() == "ss" and 
                    not body.lower().startswith("screenshot taken")):
                    print(f"    >>> SHOULD TRIGGER SCREENSHOT <<<")
                
                print()
                
            return True
            
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    check_latest_comments()