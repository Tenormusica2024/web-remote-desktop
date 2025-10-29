#!/usr/bin/env python3
"""
Simple screenshot post verification (ASCII only)
"""
import os
import requests
from pathlib import Path
from dotenv import load_dotenv
import json
from datetime import datetime

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env_private", override=True)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO", "Tenormusica2024/Private")

def check_posts():
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }
    
    url = f"https://api.github.com/repos/{GITHUB_REPO}/issues/1/comments"
    
    try:
        response = requests.get(url, headers=headers, params={"per_page": 5})
        
        if response.status_code == 200:
            comments = response.json()
            
            print("=== Recent Screenshot Posts ===")
            screenshot_count = 0
            
            for comment in comments[-5:]:  # Last 5 comments
                comment_id = comment["id"]
                author = comment["user"]["login"]
                body = comment["body"]
                created_at = comment["created_at"]
                
                # Check for screenshot-related content
                if ("screenshot taken" in body.lower() or 
                    "![screenshot]" in body or
                    "screenshots/" in body):
                    
                    screenshot_count += 1
                    print(f"\n[Screenshot Post {screenshot_count}]")
                    print(f"ID: {comment_id}")
                    print(f"Author: {author}")
                    print(f"Created: {created_at}")
                    print(f"Has image: {'YES' if '![screenshot]' in body else 'NO'}")
                    print(f"Has URL: {'YES' if 'screenshots/' in body else 'NO'}")
                    
                    # Extract image URL if present
                    if "![screenshot]" in body:
                        lines = body.split('\n')
                        for line in lines:
                            if "![screenshot]" in line:
                                print(f"Image line: {line}")
                                break
                    
                    # Save details to JSON file
                    with open(ROOT / f"post_{comment_id}.json", "w", encoding="utf-8") as f:
                        json.dump({
                            "id": comment_id,
                            "author": author,
                            "created_at": created_at,
                            "body_preview": body[:200] + "..." if len(body) > 200 else body,
                            "has_image": "![screenshot]" in body
                        }, f, ensure_ascii=False, indent=2)
            
            print(f"\nTotal screenshot posts found: {screenshot_count}")
            
            # Check title tracking
            title_file = ROOT / "last_title_content_private.txt"
            if title_file.exists():
                title = title_file.read_text(encoding='utf-8').strip()
                print(f"Last processed title: '{title}'")
                
                if "ss remote working test4" in title:
                    print("Title 'ss remote working test4' was processed successfully")
            
            return screenshot_count > 0
            
        else:
            print(f"API Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = check_posts()
    print(f"\nVerification {'PASSED' if success else 'FAILED'}")