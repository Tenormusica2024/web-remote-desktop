#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GitHub Issue コメント → Claude Code 貼り付け (Private Repository Minimal Version)
privateリポジトリ用の最小構成版（public版からのコピー＋改修）
"""

import os, sys, time, json, re
from pathlib import Path
import datetime
import requests
import pyautogui
import pyperclip

# Load environment variables with private priority
def load_env():
    """Environment variables loading - Private priority"""
    env_private = Path(__file__).parent / ".env_private"
    env_default = Path(__file__).parent / ".env"
    
    # .env_privateが存在すれば優先使用
    env_file = env_private if env_private.exists() else env_default
    
    if env_file.exists():
        print(f"[CONFIG] Loading from: {env_file}")
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    if not os.getenv(key):  # Only set if not already set
                        os.environ[key] = value

load_env()

# Configuration from environment variables
GH_REPO = os.getenv("GH_REPO")
GH_ISSUE = os.getenv("GH_ISSUE")
GH_TOKEN = os.getenv("GH_TOKEN")
POLL_SEC = int(os.getenv("POLL_SEC", "5"))
DEFAULT_PANE = os.getenv("DEFAULT_PANE", "lower").lower()
ONLY_AUTHOR = os.getenv("ONLY_AUTHOR", "").strip()

if not (GH_REPO and GH_ISSUE and GH_TOKEN):
    print("[ERROR] GH_REPO / GH_ISSUE / GH_TOKEN が未設定です。")
    sys.exit(1)

OWNER, REPO = GH_REPO.split("/", 1)
ISSUE_NUM = int(GH_ISSUE)

API = "https://api.github.com"
UA = "gh-issue-to-claude-private-minimal/1.0"

session = requests.Session()
session.headers.update({
    "Authorization": f"Bearer {GH_TOKEN}",
    "Accept": "application/vnd.github+json",
    "User-Agent": UA,
})

# State and config files - Private version
STATE_FILE = Path(".gh_issue_to_claude_state_private_minimal.json")
CFG_FILE = Path(".gh_issue_to_claude_coords_private_new.json")  # Reuse existing coords

# Utility functions
def load_json(p: Path, default):
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return default

def save_json(p: Path, obj):
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

def now_str():
    return datetime.datetime.now().strftime("%H:%M:%S")

# Claude Code operations
def focus_and_paste(pane: str, text: str, auto_enter: bool = True):
    cfg = load_json(CFG_FILE, {})
    if pane not in ("upper", "lower"):
        pane = DEFAULT_PANE
    coords = cfg.get(pane)
    if not coords:
        raise RuntimeError(f"座標未設定: {pane}. 座標ファイルが必要です: {CFG_FILE}")

    x, y = coords
    # Focus
    pyautogui.moveTo(x, y, duration=0.1)
    pyautogui.click()
    time.sleep(0.05)
    
    # Paste using clipboard
    old_clip = None
    try:
        old_clip = pyperclip.paste()
    except Exception:
        pass

    pyperclip.copy(text)
    time.sleep(0.1)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.2)
    
    # Auto-enter control
    if auto_enter:
        pyautogui.press("enter")
        time.sleep(0.1)

    # Restore clipboard
    if old_clip is not None:
        try:
            pyperclip.copy(old_clip)
        except Exception:
            pass

# GitHub polling
def conditional_get(url, etag=None):
    headers = {}
    if etag:
        headers["If-None-Match"] = etag
    r = session.get(url, headers=headers, timeout=20)
    new_etag = r.headers.get("ETag", etag)
    return r, new_etag

def parse_pane_and_text(body: str):
    """Parse pane and text from comment body"""
    s = body.strip()
    
    # noenter: prefix check
    no_enter = False
    if s.lower().startswith("noenter:"):
        no_enter = True
        s = s[8:].strip()
    
    # pane specification check
    m = re.match(r"^\s*(upper|lower)\s*:\s*(.*)$", s, flags=re.IGNORECASE | re.DOTALL)
    if m:
        pane = m.group(1).lower()
        text = m.group(2).strip()
        return pane, text, no_enter
    return DEFAULT_PANE, s, no_enter

def main():
    # Load state
    state = load_json(STATE_FILE, {"last_comment_id": 0, "comments_etag": None})
    last_id = int(state.get("last_comment_id", 0))
    comments_etag = state.get("comments_etag")

    base = f"{API}/repos/{OWNER}/{REPO}"
    issue_url = f"{base}/issues/{ISSUE_NUM}"
    comments_url = f"{issue_url}/comments?per_page=30"

    print(f"[{now_str()}] Private Repository Comment Monitor Started")
    print(f"[CONFIG] Repository: {OWNER}/{REPO} Issue #{ISSUE_NUM}")
    print(f"[CONFIG] Poll interval: {POLL_SEC}s")
    print(f"[CONFIG] Default pane: {DEFAULT_PANE}")
    print(f"[CONFIG] Author filter: {ONLY_AUTHOR or '(any)'}")
    print(f"[CONFIG] Coordinates file: {CFG_FILE}")
    print()

    # Check if coordinates file exists
    if not CFG_FILE.exists():
        print(f"[ERROR] Coordinates file not found: {CFG_FILE}")
        print("Please ensure coordinates are properly configured.")
        sys.exit(1)

    print(f"[{now_str()}] Starting polling...")

    while True:
        try:
            # Get comments with conditional request
            r, comments_etag = conditional_get(comments_url, comments_etag)
            if r.status_code == 304:
                time.sleep(POLL_SEC)
                continue
            if r.status_code != 200:
                print(f"[WARN] comments GET {r.status_code}: {r.text[:200]}")
                time.sleep(POLL_SEC)
                continue

            comments = r.json()
            # Sort by ID for chronological order
            comments.sort(key=lambda c: c.get("id", 0))
            to_process = [c for c in comments if c.get("id", 0) > last_id]

            for c in to_process:
                cid = c.get("id", 0)
                user = (c.get("user") or {}).get("login", "")
                body = c.get("body") or ""
                
                if ONLY_AUTHOR and user.lower() != ONLY_AUTHOR.lower():
                    # Process only specified author
                    last_id = max(last_id, cid)
                    continue

                pane, text, no_enter = parse_pane_and_text(body)
                if not text:
                    last_id = max(last_id, cid)
                    continue

                auto_enter = not no_enter
                enter_info = "Enter" if auto_enter else "no Enter"
                print(f"[{now_str()}] comment #{cid} by @{user} -> pane={pane}, {len(text)} chars, {enter_info}")
                
                try:
                    focus_and_paste(pane, text, auto_enter)
                    if auto_enter:
                        print(f"  -> pasted and sent (Enter pressed)")
                    else:
                        print(f"  -> pasted only (Enter skipped)")
                except Exception as e:
                    print(f"  [ERROR] paste failed: {e}")

                last_id = max(last_id, cid)

            # Save state
            state["last_comment_id"] = last_id
            state["comments_etag"] = comments_etag
            save_json(STATE_FILE, state)

        except KeyboardInterrupt:
            print("\n[INFO] Shutting down...")
            break
        except Exception as e:
            print(f"[ERROR] {e.__class__.__name__}: {e}")
            time.sleep(max(10, POLL_SEC))
        
        time.sleep(POLL_SEC)

if __name__ == "__main__":
    main()