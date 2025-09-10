#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ClaudeCode Stuck Screenshot → GitHub (minimal)
- Hotkey press (default: ctrl+alt+f12) captures screenshot
- Uploads to private repo via GitHub Contents API
- Posts/creates an Issue comment with a direct link
- Proxy: requests picks HTTP(S)_PROXY from environment automatically
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
load_dotenv(ROOT / ".env")

GITHUB_TOKEN  = os.getenv("GITHUB_TOKEN", "").strip()
GITHUB_REPO   = os.getenv("GITHUB_REPO", "").strip()       # "owner/repo"
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "main").strip()
ISSUE_NUMBER  = os.getenv("GITHUB_ISSUE_NUMBER", "").strip()
HOTKEY        = os.getenv("HOTKEY", "ctrl+alt+f12").strip()

API_BASE = "https://api.github.com"
SESSION = requests.Session()
SESSION.headers.update({
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
})

def _fail(msg):
    print(f"[ERR] {msg}", file=sys.stderr)
    sys.exit(1)

def _assert_config():
    if not GITHUB_TOKEN or not GITHUB_REPO:
        _fail("GITHUB_TOKEN / GITHUB_REPO を .env に設定してください。")

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
    # 既存 Issue が未指定なら新規作成（シンプルに一度だけ）
    if not issue:
        url = f"{API_BASE}/repos/{owner}/{repo}/issues"
        title = "ClaudeCode Stuck Shots"
        r = SESSION.post(url, json={"title": title, "body": "Auto-generated bucket for stuck screenshots."}, timeout=30)
        if r.status_code not in (200, 201):
            _fail(f"Issue create failed: {r.status_code} {r.text}")
        issue = str(r.json()["number"])
        print(f"[INFO] Created issue #{issue}")
    # コメント投稿
    url = f"{API_BASE}/repos/{owner}/{repo}/issues/{issue}/comments"
    r = SESSION.post(url, json={"body": body}, timeout=30)
    if r.status_code not in (200, 201):
        _fail(f"Comment failed: {r.status_code} {r.text}")

def take_and_upload(note: str = ""):
    _assert_config()
    png = capture_png_bytes()
    ts = datetime.now(timezone.utc).astimezone().strftime("%Y%m%d_%H%M%S")
    host = socket.gethostname()
    rel_path = f"screenshots/{datetime.now().strftime('%Y/%m')}/{ts}_{host}.png"
    msg = f"Add stuck screenshot {ts} ({host})"
    print(f"[INFO] Uploading {rel_path} ({len(png)} bytes)...")
    html_url = github_put_file(rel_path, png, msg)
    # GitHub 上で誰でも見える "?raw=1" URL（認証が必要な private でも UI からは見える）
    raw_hint = html_url + "?raw=1" if html_url else rel_path
    body = f"""**Stuck shot**
- Time: `{ts}`
- Host: `{host}`
- Note: {note or "-"}
- File: {html_url}

![stuck]({raw_hint})
"""
    ensure_issue_and_comment(body)
    print("[OK] Uploaded & commented.")

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

    print(f"[READY] Press HOTKEY: {HOTKEY}  (Ctrl+C to exit)")
    try:
        keyboard.add_hotkey(HOTKEY, lambda: take_and_upload())
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[EXIT] bye")
    except Exception as e:
        _fail(e)

if __name__ == "__main__":
    main()