#!/usr/bin/env python3
"""
Real-time GitHub Issue comment monitor with immediate response - PRIVATE REPOSITORY VERSION
This version supports private repositories with enhanced authentication
"""

import os, time, requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import pyautogui
import io, base64, socket

# Configuration - Private Repository Version
ROOT = Path(__file__).resolve().parent
# Load private repository configuration
load_dotenv(ROOT / ".env_private", override=True)
# Fallback to standard .env if private config not found
if not os.getenv("GITHUB_TOKEN"):
    load_dotenv(ROOT / ".env", override=True)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO", "Tenormusica2024/web-remote-desktop")
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "master")
MONITOR_ISSUE = "1"
POLL_INTERVAL = 10  # More frequent polling (10 seconds)

SESSION = requests.Session()
SESSION.headers.update({
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "claude-code-private-monitor/1.0"
})

LOG_FILE = ROOT / "realtime_monitor_private.log"

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {msg}"
    
    try:
        print(log_msg)
    except UnicodeEncodeError:
        # Fallback for encoding issues
        safe_msg = log_msg.encode('ascii', 'replace').decode('ascii')
        print(safe_msg)
    
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_msg + "\n")

def get_latest_comments(count=10):
    """Get latest comments without using 'since' parameter"""
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/issues/{MONITOR_ISSUE}/comments"
        
        # Get latest comments with timestamp-based header for cache-busting
        headers = SESSION.headers.copy()
        headers['Cache-Control'] = 'no-cache'
        headers['If-None-Match'] = ''  # Force refresh
        
        response = SESSION.get(url, 
                              params={"per_page": count, "sort": "created", "direction": "desc"},
                              headers=headers,
                              timeout=30)
        
        if response.status_code == 200:
            comments = response.json()
            log(f"Retrieved {len(comments)} comments from API")
            return comments
        else:
            log(f"API Error: {response.status_code} - {response.text}")
            return []
            
    except Exception as e:
        log(f"Error fetching comments: {e}")
        return []

def capture_screenshot():
    """Take screenshot and return PNG bytes"""
    shot = pyautogui.screenshot()
    buf = io.BytesIO()
    shot.save(buf, format="PNG")
    return buf.getvalue()

def upload_to_github(content_bytes, filename):
    """Upload screenshot to GitHub"""
    try:
        owner, repo = GITHUB_REPO.split("/", 1)
        path_in_repo = f"screenshots/realtime/{filename}"
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path_in_repo}"
        
        b64_content = base64.b64encode(content_bytes).decode("ascii")
        payload = {
            "message": f"Real-time screenshot: {filename}",
            "content": b64_content,
            "branch": GITHUB_BRANCH,
        }
        
        response = SESSION.put(url, json=payload, timeout=60)
        
        if response.status_code in (200, 201):
            return response.json().get("content", {}).get("html_url", "")
        else:
            log(f"Upload error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        log(f"Upload failed: {e}")
        return None

def post_reply(comment_id, screenshot_url=None):
    """Post reply comment"""
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/issues/{MONITOR_ISSUE}/comments"
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        hostname = socket.gethostname()
        
        if screenshot_url:
            body = f"""✅ **Real-time Screenshot Captured**

📸 **Screenshot**: [View Image]({screenshot_url})
🕒 **Time**: {timestamp}  
💻 **Host**: {hostname}

![screenshot]({screenshot_url}?raw=1)

*Real-time response to comment ID: {comment_id}*"""
        else:
            body = f"""✅ **Real-time Screenshot Captured**

🕒 **Time**: {timestamp}
💻 **Host**: {hostname}  
⚠️ **Note**: Screenshot taken but upload failed

*Real-time response to comment ID: {comment_id}*"""
        
        response = SESSION.post(url, json={"body": body}, timeout=30)
        
        if response.status_code in (200, 201):
            log("Reply comment posted successfully")
            return True
        else:
            log(f"Reply failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        log(f"Reply error: {e}")
        return False

def process_comment(comment):
    """Process a single screenshot request"""
    comment_id = comment["id"]
    author = comment["user"]["login"]
    body = comment["body"].strip()
    
    log(f"Processing screenshot request from {author} (ID: {comment_id})")
    
    # Take screenshot
    try:
        screenshot_data = capture_screenshot()
        size_kb = len(screenshot_data) // 1024
        log(f"Screenshot captured: {size_kb}KB")
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{socket.gethostname()}_realtime.png"
        
        # Upload to GitHub
        screenshot_url = upload_to_github(screenshot_data, filename)
        
        if screenshot_url:
            log(f"Screenshot uploaded: {screenshot_url}")
        else:
            log("Screenshot upload failed, posting reply without URL")
        
        # Post reply
        post_reply(comment_id, screenshot_url)
        
    except Exception as e:
        log(f"Screenshot processing failed: {e}")
        post_reply(comment_id, None)

def monitor_loop():
    """Main monitoring loop with immediate response - Private Repository Support"""
    log("Starting real-time GitHub comment monitor (PRIVATE VERSION)")
    log(f"Repository: {GITHUB_REPO} (Private repository supported)")
    log(f"Issue: #{MONITOR_ISSUE}")
    log(f"Poll interval: {POLL_INTERVAL} seconds")
    
    # Verify private repository access
    try:
        test_url = f"https://api.github.com/repos/{GITHUB_REPO}"
        test_response = SESSION.get(test_url, timeout=10)
        if test_response.status_code == 200:
            repo_data = test_response.json()
            repo_visibility = "private" if repo_data.get("private", False) else "public"
            log(f"Repository access verified: {repo_visibility} repository")
        else:
            log(f"Warning: Repository access test failed: {test_response.status_code}")
    except Exception as e:
        log(f"Warning: Could not verify repository access: {e}")
    
    processed_comments = set()
    
    try:
        while True:
            comments = get_latest_comments(5)
            
            for comment in reversed(comments):  # Process oldest first
                comment_id = comment["id"]
                try:
                    body = comment["body"].strip().lower()
                    author = comment["user"]["login"]
                    
                    # Check if this comment is exactly 'ss' (standalone) and hasn't been processed
                    if (comment_id not in processed_comments and 
                        body == "ss" and 
                        not body.startswith("screenshot taken") and
                        not body.startswith("real-time screenshot")):
                        
                        log(f"New 'ss' comment detected from {author}: ID {comment_id}")
                        processed_comments.add(comment_id)
                        
                        # Process immediately
                        process_comment(comment)
                except Exception as e:
                    log(f"Error processing comment {comment_id}: {e}")
            
            time.sleep(POLL_INTERVAL)
            
    except KeyboardInterrupt:
        log("Monitor stopped by user")
    except Exception as e:
        log(f"Monitor error: {e}")

if __name__ == "__main__":
    monitor_loop()