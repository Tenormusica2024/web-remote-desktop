#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Private Issue Comment -> Claude Code Paste Test
简单版本テスト用
"""

import os, sys, time, json, re
from pathlib import Path
import requests
import pyautogui
import pyperclip

# .env_private読み込み
env_file = Path(".env_private")
if env_file.exists():
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

GH_REPO = os.getenv("GH_REPO")
GH_ISSUE = os.getenv("GH_ISSUE")
GH_TOKEN = os.getenv("GH_TOKEN")

if not (GH_REPO and GH_ISSUE and GH_TOKEN):
    print("Configuration missing")
    sys.exit(1)

# 座標ファイル読み込み
coords_file = Path(".gh_issue_to_claude_coords_private_new.json")
if not coords_file.exists():
    print("Coordinates file missing")
    sys.exit(1)

coords = json.loads(coords_file.read_text(encoding="utf-8"))
lower_coords = coords.get("lower")
if not lower_coords:
    print("Lower coordinates not found")
    sys.exit(1)

print(f"Testing Private Issue paste functionality")
print(f"Repository: {GH_REPO}")
print(f"Issue: #{GH_ISSUE}")
print(f"Lower pane coordinates: {lower_coords}")

# GitHub API設定
session = requests.Session()
session.headers.update({
    "Authorization": f"Bearer {GH_TOKEN}",
    "Accept": "application/vnd.github+json",
    "User-Agent": "private-paste-test/1.0"
})

# コメント取得
comments_url = f"https://api.github.com/repos/{GH_REPO}/issues/{GH_ISSUE}/comments"
print(f"Fetching comments from: {comments_url}")

try:
    r = session.get(comments_url, timeout=10)
    print(f"API Response: {r.status_code}")
    
    if r.status_code == 200:
        comments = r.json()
        print(f"Total comments: {len(comments)}")
        
        # lower:で始まる最新コメントを検索
        lower_comments = []
        for c in comments:
            body = c.get("body", "").strip()
            if body.lower().startswith("lower:"):
                lower_comments.append(c)
        
        print(f"Comments starting with 'lower:': {len(lower_comments)}")
        
        if lower_comments:
            # 最新のlower:コメントを処理
            latest_lower = max(lower_comments, key=lambda x: x.get("id", 0))
            cid = latest_lower.get("id", 0)
            user = (latest_lower.get("user") or {}).get("login", "")
            body = latest_lower.get("body", "")
            
            print(f"Latest lower comment:")
            print(f"  ID: {cid}")
            print(f"  User: {user}")
            print(f"  Body: {body}")
            
            # lower:を除去してテキスト抽出
            text = body[6:].strip()  # "lower:"を除去
            print(f"  Text to paste: {text}")
            
            if text:
                print(f"Attempting to paste to lower pane...")
                
                # Claude Code下ペインにフォーカス
                x, y = lower_coords
                pyautogui.moveTo(x, y, duration=0.2)
                pyautogui.click()
                time.sleep(0.1)
                
                # クリップボード経由で貼り付け
                old_clip = None
                try:
                    old_clip = pyperclip.paste()
                except:
                    pass
                
                pyperclip.copy(text)
                time.sleep(0.1)
                pyautogui.hotkey("ctrl", "v")
                time.sleep(0.2)
                pyautogui.press("enter")
                time.sleep(0.1)
                
                # クリップボード復元
                if old_clip:
                    try:
                        pyperclip.copy(old_clip)
                    except:
                        pass
                
                print(f"SUCCESS: Text pasted to lower pane and Enter pressed")
            else:
                print("No text to paste")
        else:
            print("No comments starting with 'lower:' found")
    else:
        print(f"API Error: {r.text[:200]}")
        
except Exception as e:
    print(f"Exception: {e}")

print("Test completed")