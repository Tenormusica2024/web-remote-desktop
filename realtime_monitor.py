#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Real-time comment monitoring and processing
"""
import os
import sys
import time
import json
import requests
from datetime import datetime
from pathlib import Path

def setup_environment():
    """Setup environment variables"""
    env_vars = {
        'GH_REPO': 'Tenormusica2024/web-remote-desktop',
        'GH_ISSUE': '3',
        'GH_TOKEN': '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',
        'POLL_SEC': '2',  # 2秒間隔で高速チェック
        'DEFAULT_PANE': 'lower',
        'ONLY_AUTHOR': 'Tenormusica2024'
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value

def monitor_and_process_comments(duration_seconds=90):
    """Monitor and process comments for specified duration"""
    setup_environment()
    
    from gh_issue_to_claude_paste import (
        parse_pane_and_text, 
        focus_and_paste,
        session,
        load_json,
        save_json,
        STATE_FILE,
        API,
        OWNER,
        REPO,
        ISSUE_NUM
    )
    
    print("=== Real-time Comment Monitor ===")
    print(f"Start time: {datetime.now().strftime('%H:%M:%S')}")
    print(f"Duration: {duration_seconds} seconds")
    print(f"Poll interval: 2 seconds")
    print(f"Target: Issue #{ISSUE_NUM}")
    print("=" * 40)
    
    # Load current state
    state = load_json(STATE_FILE, {"last_comment_id": 0, "comments_etag": None})
    last_id = int(state.get("last_comment_id", 0))
    comments_etag = state.get("comments_etag")
    
    print(f"Starting from comment ID: {last_id}")
    print("Waiting for new comments...")
    print()
    
    comments_url = f"{API}/repos/{OWNER}/{REPO}/issues/{ISSUE_NUM}/comments?per_page=10"
    start_time = time.time()
    
    while time.time() - start_time < duration_seconds:
        try:
            # Get comments with ETag
            headers = {}
            if comments_etag:
                headers["If-None-Match"] = comments_etag
            
            r = session.get(comments_url, headers=headers, timeout=10)
            new_etag = r.headers.get("ETag", comments_etag)
            
            if r.status_code == 304:
                # No new comments
                remaining = int(duration_seconds - (time.time() - start_time))
                print(f"\rWaiting... {remaining}s remaining", end="", flush=True)
                time.sleep(2)
                continue
            
            if r.status_code != 200:
                print(f"\nAPI Error: {r.status_code}")
                time.sleep(5)
                continue
            
            comments = r.json()
            comments.sort(key=lambda c: c.get("id", 0))
            new_comments = [c for c in comments if c.get("id", 0) > last_id]
            
            if new_comments:
                print(f"\n🔔 NEW COMMENTS DETECTED: {len(new_comments)}")
                
                for c in new_comments:
                    cid = c.get("id", 0)
                    user = c.get("user", {}).get("login", "")
                    body = c.get("body", "")
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    
                    print(f"\n[{timestamp}] Processing comment #{cid}")
                    print(f"  User: @{user}")
                    print(f"  Body: {repr(body)}")
                    
                    # Skip if not target user
                    if user.lower() != os.environ.get('ONLY_AUTHOR', '').lower():
                        print(f"  ⏭️  Skipped (not target user)")
                        last_id = max(last_id, cid)
                        continue
                    
                    # Parse comment
                    pane, text, no_enter = parse_pane_and_text(body)
                    if not text.strip():
                        print(f"  ⏭️  Skipped (empty text)")
                        last_id = max(last_id, cid)
                        continue
                    
                    auto_enter = not no_enter
                    enter_info = "Auto Enter" if auto_enter else "No Enter"
                    
                    print(f"  📍 Target: {pane.upper()} pane")
                    print(f"  📝 Text: {repr(text)} ({len(text)} chars)")
                    print(f"  ⌨️  Action: {enter_info}")
                    
                    # Execute the paste operation
                    try:
                        focus_and_paste(pane, text, auto_enter)
                        if auto_enter:
                            print(f"  ✅ SUCCESS: Pasted and sent (Enter pressed)")
                        else:
                            print(f"  ✅ SUCCESS: Pasted only (Enter skipped)")
                    except Exception as e:
                        print(f"  ❌ ERROR: {e}")
                    
                    last_id = max(last_id, cid)
                
                # Update state
                state["last_comment_id"] = last_id
                state["comments_etag"] = new_etag
                save_json(STATE_FILE, state)
                print(f"\n💾 State updated: processed up to ID {last_id}")
            
            else:
                remaining = int(duration_seconds - (time.time() - start_time))
                print(f"\rWaiting... {remaining}s remaining", end="", flush=True)
            
            time.sleep(2)
            
        except KeyboardInterrupt:
            print(f"\n⏹️  Manual stop")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            time.sleep(5)
    
    elapsed = time.time() - start_time
    print(f"\n\n=== Monitoring Complete ===")
    print(f"Duration: {elapsed:.1f} seconds")
    print(f"Final processed ID: {last_id}")
    print("Ready for next test!")

if __name__ == "__main__":
    monitor_and_process_comments(90)  # 90秒間監視