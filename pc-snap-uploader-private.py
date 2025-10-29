#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Claude Code Private Screenshot → GitHub Uploader (Private Edition)
- Hotkey press (default: ctrl+alt+f12) captures screenshot
- Uploads to Tenormusica2024/Private repo via GitHub Contents API
- Posts/creates an Issue comment with a direct link
- Private repository専用版
"""

import os, io, sys, time, base64, socket, argparse
from datetime import datetime, timezone
from pathlib import Path

import requests
import pyautogui

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = lambda *a, **k: None

# ---------- Config ----------
ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env_private")

GITHUB_TOKEN  = os.getenv("GH_TOKEN", "").strip()  # Private版では GH_TOKEN を使用
GITHUB_REPO   = os.getenv("GITHUB_REPO", "Tenormusica2024/Private").strip()
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "master").strip()
ISSUE_NUMBER  = os.getenv("MONITOR_ISSUE_NUMBER", "1").strip()
HOTKEY        = os.getenv("HOTKEY", "ctrl+alt+f12").strip()

API_BASE = "https://api.github.com"
SESSION = requests.Session()
SESSION.headers.update({
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "pc-snap-uploader-private/1.0"
})

def _fail(msg):
    print(f"[ERR] {msg}", file=sys.stderr)
    sys.exit(1)

def _assert_config():
    if not GITHUB_TOKEN or not GITHUB_REPO:
        _fail("GH_TOKEN / GITHUB_REPO を .env_private に設定してください。")

def capture_png_bytes():
    shot = pyautogui.screenshot()  # full screen
    buf = io.BytesIO()
    # PNG 無劣化。サイズを抑えたい場合は JPEG へ変更可
    shot.save(buf, format="PNG")
    return buf.getvalue()

def github_put_file(path_in_repo: str, content_bytes: bytes, message: str):
    """
    PUT /repos/{owner}/{repo}/contents/{path}
    """
    owner, repo = GITHUB_REPO.split("/", 1)
    url = f"{API_BASE}/repos/{owner}/{repo}/contents/{path_in_repo}"
    b64 = base64.b64encode(content_bytes).decode("ascii")
    payload = {
        "message": message,
        "content": b64,
        "branch" : GITHUB_BRANCH,
    }
    r = SESSION.put(url, json=payload, timeout=60)
    if r.status_code not in (200, 201):
        _fail(f"GitHub upload failed: {r.status_code} {r.text}")
    data = r.json()
    # ブラウザで見える blob URL（private でもログインしていれば見える）
    html_url = data.get("content", {}).get("html_url")
    return html_url

def ensure_issue_and_comment(body: str) -> None:
    owner, repo = GITHUB_REPO.split("/", 1)
    issue = ISSUE_NUMBER
    
    # Private repositoryの既存Issue #1に投稿
    # コメント投稿
    url = f"{API_BASE}/repos/{owner}/{repo}/issues/{issue}/comments"
    r = SESSION.post(url, json={"body": body}, timeout=30)
    if r.status_code not in (200, 201):
        _fail(f"Comment failed: {r.status_code} {r.text}")
    
    print(f"[INFO] Posted comment to Private Issue #{issue}")

def take_and_upload(note: str = ""):
    _assert_config()
    png = capture_png_bytes()
    ts = datetime.now(timezone.utc).astimezone().strftime("%Y%m%d_%H%M%S")
    host = socket.gethostname()
    rel_path = f"private_screenshots/{datetime.now().strftime('%Y/%m')}/{ts}_{host}_private.png"
    msg = f"Add private screenshot {ts} ({host})"
    print(f"[INFO] Uploading to Private repo: {rel_path} ({len(png)} bytes)...")
    html_url = github_put_file(rel_path, png, msg)
    # GitHub 上で誰でも見える "?raw=1" URL（認証が必要な private でも UI からは見える）
    raw_hint = html_url + "?raw=1" if html_url else rel_path
    body = f"""**Private Screenshot**
- Time: `{ts}`
- Host: `{host}`
- Note: {note or "-"}
- File: {html_url}

![screenshot]({raw_hint})
"""
    ensure_issue_and_comment(body)
    print("[OK] Uploaded to Private repo & commented.")

def main():
    import keyboard  # global hotkey
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="Capture once and exit (no hotkey)")
    parser.add_argument("--note", type=str, default="", help="Optional note to include in comment")
    args = parser.parse_args()

    _assert_config()

    if args.once:
        take_and_upload(args.note)
        return

    print(f"[READY] Private Screenshot Uploader")
    print(f"Press HOTKEY: {HOTKEY}  (Ctrl+C to exit)")
    print(f"Target: {GITHUB_REPO} Issue #{ISSUE_NUMBER}")
    try:
        keyboard.add_hotkey(HOTKEY, lambda: take_and_upload())
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[EXIT] Private Screenshot Uploader stopped")
    except Exception as e:
        _fail(e)

if __name__ == "__main__":
    main()