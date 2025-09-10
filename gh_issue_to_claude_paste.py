#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GitHub Issue コメント → Claude Code(右上/右下) へ貼り付け＋Enter
- Webhook不要：ETagつきポーリング（超低負荷）
- 1ファイル・キャリブレーション内蔵（座標クリック方式）
- 日本語/長文OK：クリップボード経由で貼り付け

使い方:
  pip install requests pyautogui pyperclip pillow
  環境変数 GH_REPO, GH_ISSUE, GH_TOKEN（任意: POLL_SEC, DEFAULT_PANE, ONLY_AUTHOR）
  初回: python gh_issue_to_claude_paste.py --calibrate
  常駐: python gh_issue_to_claude_paste.py

コメント例:
  upper: これを右上に送って
  lower: これは右下に送って
  (プレフィックスなしは DEFAULT_PANE へ)
"""

import os, sys, time, json, io, re
from pathlib import Path
import datetime
import requests
import pyautogui
import pyperclip

# ====== 設定（環境変数） ======
GH_REPO   = os.getenv("GH_REPO")            # "owner/repo"
GH_ISSUE  = os.getenv("GH_ISSUE")           # "123"
GH_TOKEN  = os.getenv("GH_TOKEN")           # PAT
POLL_SEC  = int(os.getenv("POLL_SEC", "5")) # ポーリング間隔
DEFAULT_PANE = os.getenv("DEFAULT_PANE", "lower").lower()  # upper/lower
ONLY_AUTHOR  = os.getenv("ONLY_AUTHOR", "").strip()        # その人のコメントだけ処理（空なら全員）

if not (GH_REPO and GH_ISSUE and GH_TOKEN):
    print("[ERROR] GH_REPO / GH_ISSUE / GH_TOKEN が未設定です。環境変数をセットしてください。")
    sys.exit(1)

OWNER, REPO = GH_REPO.split("/", 1)
ISSUE_NUM   = int(GH_ISSUE)

API = "https://api.github.com"
UA  = "gh-issue-to-claude/1.0"

session = requests.Session()
session.headers.update({
    "Authorization": f"Bearer {GH_TOKEN}",
    "Accept": "application/vnd.github+json",
    "User-Agent": UA,
})

STATE_FILE = Path(".gh_issue_to_claude_state.json")   # 既読管理
CFG_FILE   = Path(".gh_issue_to_claude_coords.json")  # 座標管理

# ====== ユーティリティ ======
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

# ====== キャリブレーション ======
def calibrate():
    print("=== キャリブレーション開始 ===")
    print("手順：指示のたびに『対象の入力欄にマウスを置いて Enter』してください。")
    input("準備ができたら Enter...")

    print("\n1) 右上（upper）入力欄にマウスを置いて Enter...")
    input()
    x1, y1 = pyautogui.position()
    print(f"  → 記録 upper = ({x1}, {y1})")

    print("\n2) 右下（lower）入力欄にマウスを置いて Enter...")
    input()
    x2, y2 = pyautogui.position()
    print(f"  → 記録 lower = ({x2}, {y2})")

    cfg = {"upper": [x1, y1], "lower": [x2, y2]}
    save_json(CFG_FILE, cfg)
    print("\n✅ 保存しました:", CFG_FILE.resolve())
    print("閉じてOKです。")
    sys.exit(0)

# ====== Claude Code操作 ======
def focus_and_paste(pane: str, text: str, auto_enter: bool = True):
    cfg = load_json(CFG_FILE, {})
    if pane not in ("upper", "lower"):
        pane = DEFAULT_PANE
    coords = cfg.get(pane)
    if not coords:
        raise RuntimeError(f"座標未設定: {pane}. 先に --calibrate を実行してください。")

    x, y = coords
    # フォーカス
    pyautogui.moveTo(x, y, duration=0.1)
    pyautogui.click()
    time.sleep(0.05)
    
    # 貼り付け（日本語/長文もOK）
    old_clip = None
    try:
        old_clip = pyperclip.paste()
    except Exception:
        pass

    pyperclip.copy(text)
    time.sleep(0.1)  # クリップボードに確実に保存されるまで待機
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.2)  # 貼り付けが完了するまで待機
    
    # Enterキーを押すかどうかを制御
    if auto_enter:
        pyautogui.press("enter")
        time.sleep(0.1)  # Enterキーの処理完了まで待機

    # クリップボード復元（任意）
    if old_clip is not None:
        try:
            pyperclip.copy(old_clip)
        except Exception:
            pass

# ====== GitHubポーリング ======
def conditional_get(url, etag=None):
    headers = {}
    if etag:
        headers["If-None-Match"] = etag
    r = session.get(url, headers=headers, timeout=20)
    new_etag = r.headers.get("ETag", etag)
    return r, new_etag

def parse_pane_and_text(body: str):
    """
    'upper: text' / 'lower: text' を最優先で解釈。
    'noenter:' プレフィックスがあればEnterキーを押さない。
    無ければ DEFAULT_PANE で全文送る。
    """
    s = body.strip()
    
    # noenter: プレフィックスをチェック
    no_enter = False
    if s.lower().startswith("noenter:"):
        no_enter = True
        s = s[8:].strip()  # "noenter:" を除去
    
    # pane指定をチェック
    m = re.match(r"^\s*(upper|lower)\s*:\s*(.*)$", s, flags=re.IGNORECASE | re.DOTALL)
    if m:
        pane = m.group(1).lower()
        text = m.group(2).strip()
        return pane, text, no_enter
    return DEFAULT_PANE, s, no_enter

def main():
    if "--calibrate" in sys.argv:
        calibrate()

    state = load_json(STATE_FILE, {"last_comment_id": 0, "comments_etag": None})
    last_id = int(state.get("last_comment_id", 0))
    comments_etag = state.get("comments_etag")

    base = f"{API}/repos/{OWNER}/{REPO}"
    issue_url   = f"{base}/issues/{ISSUE_NUM}"
    comments_url= f"{issue_url}/comments?per_page=30"  # 直近を見れば十分

    print(f"[{now_str()}] Start polling: {OWNER}/{REPO} Issue #{ISSUE_NUM} every {POLL_SEC}s")
    print(f"[INFO] DEFAULT_PANE={DEFAULT_PANE}  ONLY_AUTHOR={ONLY_AUTHOR or '(any)'}")

    while True:
        try:
            # コメント一覧を条件付きGET
            r, comments_etag = conditional_get(comments_url, comments_etag)
            if r.status_code == 304:
                time.sleep(POLL_SEC); continue
            if r.status_code != 200:
                print(f"[WARN] comments GET {r.status_code}: {r.text[:200]}")
                time.sleep(POLL_SEC); continue

            comments = r.json()
            # 古い→新しい順で処理したいので昇順に並べ替え
            comments.sort(key=lambda c: c.get("id", 0))
            to_process = [c for c in comments if c.get("id", 0) > last_id]

            for c in to_process:
                cid   = c.get("id", 0)
                user  = (c.get("user") or {}).get("login", "")
                body  = c.get("body") or ""
                if ONLY_AUTHOR and user.lower() != ONLY_AUTHOR.lower():
                    # 指定ユーザーのみ処理
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

            # 状態保存
            state["last_comment_id"] = last_id
            state["comments_etag"] = comments_etag
            save_json(STATE_FILE, state)

        except KeyboardInterrupt:
            print("\nBye.")
            break
        except Exception as e:
            print(f"[ERROR] {e.__class__.__name__}: {e}")
            time.sleep(max(10, POLL_SEC))
        time.sleep(POLL_SEC)

if __name__ == "__main__":
    main()