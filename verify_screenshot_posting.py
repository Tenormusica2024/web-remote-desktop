#!/usr/bin/env python3
"""
スクリーンショット投稿の確認（UTF-8で安全に処理）
"""
import os
import requests
from pathlib import Path
from dotenv import load_dotenv
import json

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env_private", override=True)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO", "Tenormusica2024/Private")

def verify_screenshot_posts():
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }
    
    url = f"https://api.github.com/repos/{GITHUB_REPO}/issues/1/comments"
    
    try:
        response = requests.get(url, headers=headers, params={"per_page": 10, "sort": "created", "direction": "desc"})
        
        if response.status_code == 200:
            comments = response.json()
            
            print("=== Screenshot Posts Verification ===")
            screenshot_posts = []
            
            for comment in comments:
                comment_id = comment["id"]
                author = comment["user"]["login"]
                body = comment["body"]
                created_at = comment["created_at"]
                
                # スクリーンショット関連のコメントを検出
                if ("screenshot taken" in body.lower() or 
                    "auto-captured" in body.lower() or
                    "![screenshot]" in body):
                    
                    screenshot_posts.append({
                        "id": comment_id,
                        "author": author,
                        "created_at": created_at,
                        "has_image": "![screenshot]" in body,
                        "has_url": "screenshots/" in body
                    })
                    
                    print(f"\n📸 Screenshot Post Found:")
                    print(f"  ID: {comment_id}")
                    print(f"  Author: {author}")
                    print(f"  Created: {created_at}")
                    print(f"  Has image: {'✅' if '![screenshot]' in body else '❌'}")
                    print(f"  Has URL: {'✅' if 'screenshots/' in body else '❌'}")
                    
                    # 最新のタイトル変更時間と比較するため、ファイル情報を保存
                    with open(ROOT / f"screenshot_post_{comment_id}.json", "w", encoding="utf-8") as f:
                        json.dump({
                            "id": comment_id,
                            "author": author,
                            "created_at": created_at,
                            "body_length": len(body),
                            "has_image": "![screenshot]" in body,
                            "has_url": "screenshots/" in body
                        }, f, ensure_ascii=False, indent=2)
            
            print(f"\n📊 Summary:")
            print(f"  Total screenshot posts found: {len(screenshot_posts)}")
            
            if screenshot_posts:
                latest_post = screenshot_posts[0]
                print(f"  Latest screenshot post: {latest_post['created_at']}")
                print(f"  Latest post has image: {'✅' if latest_post['has_image'] else '❌'}")
                
                # タイトル変更時間と比較
                title_file = ROOT / "last_title_content_private.txt"
                if title_file.exists():
                    title_content = title_file.read_text(encoding='utf-8').strip()
                    print(f"  Last title processed: '{title_content}'")
                    
                    if "ss remote working test4" in title_content:
                        print("  ✅ Title change 'ss remote working test4' was processed")
                        print("  ✅ Screenshot should have been posted after this title change")
                    
            return len(screenshot_posts) > 0
            
        else:
            print(f"❌ API Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return False

if __name__ == "__main__":
    verify_screenshot_posts()