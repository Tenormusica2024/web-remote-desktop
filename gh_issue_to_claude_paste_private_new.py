#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GitHub Private Issue コメント → Claude Code(右上/右下) へ貼り付け＋Enter (PRIVATE VERSION)
- Webhook不要：ETagつきポーリング（超低負荷）
- Private repository専用版
- 日本語/長文OK：クリップボード経由で貼り付け

使い方:
  pip install requests pyautogui pyperclip pillow
  .env_privateファイル設定必須
  初回: python gh_issue_to_claude_paste_private_new.py --calibrate
  常駐: python gh_issue_to_claude_paste_private_new.py

コメント例:
  upper: これを右上に送って
  lower: これは右下に送って
  noenter: lower: Enterキーなしで貼り付けのみ
  (プレフィックスなしは DEFAULT_PANE へ)
"""

import os, sys, time, json, io, re
from pathlib import Path
import datetime
import requests
import pyautogui
import pyperclip

# Private repository用環境設定ロード（.env_private優先）
def load_env():
    """Private repository configuration loader with priority"""
    env_private = Path(__file__).parent / ".env_private"
    env_default = Path(__file__).parent / ".env"
    
    # .env_privateが存在すれば優先使用
    env_file = env_private if env_private.exists() else env_default
    
    if env_file.exists():
        print(f"[設定] 環境設定ファイル: {env_file.name}")
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    if not os.getenv(key):  # 既存環境変数は優先
                        os.environ[key] = value
    else:
        print("[警告] 設定ファイルが見つかりません: .env_private または .env")

load_env()

# ====== 設定（環境変数） ======
GH_REPO   = os.getenv("GH_REPO")            # "owner/repo"
GH_ISSUE  = os.getenv("GH_ISSUE")           # "123"
GH_TOKEN  = os.getenv("GH_TOKEN")           # PAT
POLL_SEC  = int(os.getenv("POLL_SEC", "5")) # ポーリング間隔
DEFAULT_PANE = os.getenv("DEFAULT_PANE", "lower").lower()  # upper/lower
ONLY_AUTHOR  = os.getenv("ONLY_AUTHOR", "").strip()        # その人のコメントだけ処理（空なら全員）

if not (GH_REPO and GH_ISSUE and GH_TOKEN):
    print("[エラー] Private repository用設定が不足しています:")
    if not GH_REPO: print("  - GH_REPO (Private repositoryのowner/repo)")
    if not GH_ISSUE: print("  - GH_ISSUE (Issue番号)")
    if not GH_TOKEN: print("  - GH_TOKEN (Personal Access Token)")
    print("\n.env_privateファイルを作成して設定してください。")
    sys.exit(1)

OWNER, REPO = GH_REPO.split("/", 1)
ISSUE_NUM   = int(GH_ISSUE)

API = "https://api.github.com"
UA  = "gh-issue-to-claude-private/1.0"

session = requests.Session()
session.headers.update({
    "Authorization": f"Bearer {GH_TOKEN}",
    "Accept": "application/vnd.github+json",
    "User-Agent": UA,
})

STATE_FILE = Path(".gh_issue_to_claude_state_private_new.json")   # 既読管理
CFG_FILE   = Path(".gh_issue_to_claude_coords_private_new.json")  # 座標管理

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
    print("=== Private Repository版 キャリブレーション開始 ===")
    print("手順：指示のたびに『Claude Code対象入力欄にマウスを置いて Enter』してください。")
    input("準備ができたら Enter...")

    print("\n1) Claude Code右上（upper）入力欄にマウスを置いて Enter...")
    input()
    x1, y1 = pyautogui.position()
    print(f"  → 記録 upper = ({x1}, {y1})")

    print("\n2) Claude Code右下（lower）入力欄にマウスを置いて Enter...")
    input()
    x2, y2 = pyautogui.position()
    print(f"  → 記録 lower = ({x2}, {y2})")

    cfg = {"upper": [x1, y1], "lower": [x2, y2]}
    save_json(CFG_FILE, cfg)
    print(f"\n✅ Private版設定ファイルに保存: {CFG_FILE.resolve()}")
    print("設定完了！キャリブレーションを終了します。")
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

    print(f"[{now_str()}] Private Issue監視開始: {OWNER}/{REPO} Issue #{ISSUE_NUM} ({POLL_SEC}秒間隔)")
    print(f"[設定] デフォルトpane={DEFAULT_PANE}  対象ユーザー={ONLY_AUTHOR or '全ユーザー'}")
    print(f"[設定] 座標ファイル={CFG_FILE}  状態ファイル={STATE_FILE}")
    print("[INFO] スクリプト起動完了。Private Issue #1のコメントを監視中...")
    print()

    while True:
        try:
            # コメント一覧を条件付きGET
            print(f"[デバッグ] API リクエスト中: {comments_url}")
            r, comments_etag = conditional_get(comments_url, comments_etag)
            if r.status_code == 304:
                print(f"[デバッグ] 304 Not Modified - 変更なし")
                time.sleep(POLL_SEC); continue
            if r.status_code != 200:
                print(f"[警告] Private API応答エラー {r.status_code}: {r.text[:200]}")
                time.sleep(POLL_SEC); continue

            comments = r.json()
            print(f"[デバッグ] 取得コメント数: {len(comments)}")
            if comments:
                latest_comment = max(comments, key=lambda c: c.get("id", 0))
                print(f"[デバッグ] 最新コメントID: {latest_comment.get('id', 0)}, 現在の last_id: {last_id}")
            
            # 古い→新しい順で処理したいので昇順に並べ替え
            comments.sort(key=lambda c: c.get("id", 0))
            to_process = [c for c in comments if c.get("id", 0) > last_id]
            print(f"[デバッグ] 処理対象コメント数: {len(to_process)}")

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
                # Unicodeセーフな出力
                safe_user = user.encode('ascii', 'replace').decode('ascii')
                safe_text = text.replace('\U0001f916', '[ROBOT]').replace('\u2705', '[CHECK]')[:80]
                safe_text = safe_text.encode('ascii', 'replace').decode('ascii')
                print(f"[{now_str()}] Private Issue comment #{cid} by @{safe_user}")
                print(f"  送信先pane: {pane}, 文字数: {len(text)}, {enter_info}")
                print(f"  内容: {safe_text}{'...' if len(text) > 80 else ''}")
                try:
                    focus_and_paste(pane, text, auto_enter)
                    if auto_enter:
                        print(f"  ✅ 貼り付け＆Enter送信完了")
                    else:
                        print(f"  ✅ 貼り付けのみ完了（Enter省略）")
                except Exception as e:
                    print(f"  ❌ 送信エラー: {e}")

                last_id = max(last_id, cid)

            # 状態保存
            state["last_comment_id"] = last_id
            state["comments_etag"] = comments_etag
            save_json(STATE_FILE, state)

        except KeyboardInterrupt:
            print(f"\n[{now_str()}] ユーザー中断。Private Issue監視を終了します。")
            break
        except Exception as e:
            print(f"[エラー] 予期しないエラー: {e.__class__.__name__}: {e}")
            time.sleep(max(10, POLL_SEC))
        time.sleep(POLL_SEC)

if __name__ == "__main__":
    main()