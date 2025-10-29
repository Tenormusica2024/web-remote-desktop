#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Screenshot Monitor for Private Repository
- GitHub Issueタイトル変更時のみスクリーンショット撮影・投稿
- Claude Codeへの送信なし（GitHub Issue内のみで完結）
"""

import os, time, sys
from datetime import datetime
from pathlib import Path
import requests
import pyautogui
import io, base64, socket

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = lambda *a, **k: None

# ---------- Config ----------
ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env_private", override=True)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO", "Tenormusica2024/Private")
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "main")
MONITOR_ISSUE = "1"
POLL_INTERVAL = 30  # 秒

API_BASE = "https://api.github.com"
LAST_TITLE_FILE = ROOT / "last_title_simple.txt"
LOG_FILE = ROOT / "simple_monitor.log"

SESSION = requests.Session()
SESSION.headers.update({
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
})

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {msg}"
    try:
        print(log_msg)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_msg + "\n")
    except:
        pass

def check_title_change():
    """Issueタイトル変更を監視（ssキーワード検知時のみスクリーンショット）"""
    try:
        url = f"{API_BASE}/repos/{GITHUB_REPO}/issues/{MONITOR_ISSUE}"
        r = SESSION.get(url, timeout=30)
        
        if r.status_code != 200:
            log(f"API Error: {r.status_code}")
            return False
            
        issue_data = r.json()
        title = issue_data.get("title", "").strip().lower()
        
        # 「ss」を含むタイトルのみ処理
        if "ss" in title:
            current_title = title.strip()
            
            # 重複チェック
            if LAST_TITLE_FILE.exists():
                last_title = LAST_TITLE_FILE.read_text(encoding='utf-8').strip()
                if last_title == current_title:
                    return True  # 既に処理済み
                    
            # 新しいタイトルを記録
            LAST_TITLE_FILE.write_text(current_title, encoding='utf-8')
            log(f"Title change detected: {current_title}")
            
            # スクリーンショット実行
            take_and_post_screenshot(title)
            
        return True
        
    except Exception as e:
        log(f"Error checking title: {e}")
        return False

def capture_screenshot():
    """スクリーンショット撮影"""
    shot = pyautogui.screenshot()
    buf = io.BytesIO()
    shot.save(buf, format="PNG")
    return buf.getvalue()

def upload_to_github(png_data, filename):
    """GitHubにファイルアップロード"""
    owner, repo = GITHUB_REPO.split("/", 1)
    url = f"{API_BASE}/repos/{owner}/{repo}/contents/screenshots/{filename}"
    b64 = base64.b64encode(png_data).decode("ascii")
    
    payload = {
        "message": f"Screenshot: {filename}",
        "content": b64,
        "branch": GITHUB_BRANCH,
    }
    
    r = SESSION.put(url, json=payload, timeout=60)
    if r.status_code not in (200, 201):
        raise Exception(f"Upload failed: {r.status_code}")
    return r.json().get("content", {}).get("html_url")

def post_screenshot_comment(image_url, filename):
    """GitHub Issueにスクリーンショット投稿"""
    url = f"{API_BASE}/repos/{GITHUB_REPO}/issues/{MONITOR_ISSUE}/comments"
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # シンプルなコメント（Claude Codeへの送信なし）
    body = f"![screenshot]({image_url}?raw=1)"
    
    r = SESSION.post(url, json={"body": body}, timeout=30)
    if r.status_code in (200, 201):
        log(f"Screenshot posted: {filename}")
        return True
    else:
        log(f"Post failed: {r.status_code}")
        return False

def take_and_post_screenshot(title):
    """スクリーンショット撮影・投稿"""
    try:
        log("Taking screenshot...")
        
        # スクリーンショット撮影
        png_data = capture_screenshot()
        size_kb = len(png_data) // 1024
        log(f"Screenshot captured: {size_kb}KB")
        
        # ファイル名生成
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{ts}_screenshot.png"
        
        # GitHubにアップロード
        image_url = upload_to_github(png_data, filename)
        log(f"Uploaded: {image_url}")
        
        # GitHub Issueに投稿
        post_screenshot_comment(image_url, filename)
        
    except Exception as e:
        log(f"Screenshot failed: {e}")

def main_loop():
    """メインループ"""
    if not GITHUB_TOKEN or not GITHUB_REPO:
        log("ERROR: GITHUB_TOKEN or GITHUB_REPO not configured")
        sys.exit(1)
        
    log("Starting simple screenshot monitor...")
    log(f"Repository: {GITHUB_REPO}")
    log(f"Issue: #{MONITOR_ISSUE}")
    log(f"Poll interval: {POLL_INTERVAL}s")
    
    try:
        while True:
            check_title_change()
            time.sleep(POLL_INTERVAL)
            
    except KeyboardInterrupt:
        log("Monitor stopped by user")
    except Exception as e:
        log(f"Monitor crashed: {e}")

if __name__ == "__main__":
    main_loop()