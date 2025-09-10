#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Remote Screenshot Monitor via GitHub Issues
- 社内PCからGitHub Issueに「screenshot」コメント → 自宅PCが検知して自動撮影
- バックグラウンド監視サービス（常駐型）
"""

import os, time, json, sys
from datetime import datetime, timezone
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
# load_dotenv(ROOT / ".env")  # 一時的に無効化

# 直接設定
GITHUB_TOKEN = "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"
GITHUB_REPO = "Tenormusica2024/web-remote-desktop"
GITHUB_BRANCH = "master"
MONITOR_ISSUE = "1"  # 監視対象Issue番号
POLL_INTERVAL = 30  # 秒

API_BASE = "https://api.github.com"
LAST_COMMENT_FILE = ROOT / "last_comment_id.txt"
LAST_TITLE_FILE = ROOT / "last_title_content.txt"
LOG_FILE = ROOT / "monitor.log"

# グローバル変数：処理中のタイトルを追跡
PROCESSING_TITLE_HASH = None

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
    except UnicodeEncodeError:
        # ASCII文字のみでログ出力
        ascii_msg = log_msg.encode('ascii', 'replace').decode('ascii')
        print(ascii_msg)
    
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_msg + "\n")

def _fail(msg):
    log(f"ERROR: {msg}")
    sys.exit(1)

def _assert_config():
    if not GITHUB_TOKEN or not GITHUB_REPO:
        _fail("GITHUB_TOKEN / GITHUB_REPO を .env に設定してください")
    if not MONITOR_ISSUE:
        _fail("MONITOR_ISSUE_NUMBER を .env に設定してください（監視対象のIssue番号）")

def get_last_comment_id():
    """最後に処理したコメントIDを取得"""
    try:
        if LAST_COMMENT_FILE.exists():
            return int(LAST_COMMENT_FILE.read_text().strip())
        return 0
    except:
        return 0

def save_last_comment_id(comment_id):
    """最後に処理したコメントIDを保存"""
    LAST_COMMENT_FILE.write_text(str(comment_id))

def check_issue_title():
    """Issueタイトルでスクリーンショット指示をチェック"""
    try:
        owner, repo = GITHUB_REPO.split("/", 1)
        url = f"{API_BASE}/repos/{owner}/{repo}/issues/{MONITOR_ISSUE}"
        
        r = SESSION.get(url, timeout=30)
        if r.status_code != 200:
            log(f"GitHub API error (title check): {r.status_code} {r.text}")
            return False
            
        issue_data = r.json()
        title = issue_data.get("title", "").strip().lower()
        author = issue_data.get("user", {}).get("login", "unknown")
        updated_at = issue_data.get("updated_at", "")
        
        # タイトルでスクリーンショット指示を検知（「ss」のみ）
        if "ss" in title:
            # タイトル内容のみで重複チェック（updated_atは使わない）
            current_title_content = title.strip()
            
            # グローバル変数でも重複チェック（処理中の場合はスキップ）
            global PROCESSING_TITLE_HASH
            if PROCESSING_TITLE_HASH == current_title_content:
                return True  # 既に処理中
            
            # ファイルでも重複チェック（既に処理済みならスキップ）
            try:
                if LAST_TITLE_FILE.exists():
                    last_title_content = LAST_TITLE_FILE.read_text(encoding='utf-8').strip()
                    if last_title_content == current_title_content:
                        # 既に処理済み - ログに記録せず静かにスキップ
                        return True
            except Exception as e:
                log(f"Error reading last title file: {e}")
                
            # 処理開始をマーク
            PROCESSING_TITLE_HASH = current_title_content
            
            # 新しいタイトル内容を保存（実行前に保存して重複防止）
            try:
                LAST_TITLE_FILE.write_text(current_title_content, encoding='utf-8')
                log(f"Processing new title command: {current_title_content}")
            except Exception as e:
                log(f"Error saving title content: {e}")
                
            # 短時間スリープで他の同時処理を防ぐ
            time.sleep(1)
            
            # コマンド実行
            cmd = {
                "id": f"title_{updated_at}",
                "author": author,
                "body": f"Title command: {title}",
                "created_at": updated_at,
                "url": issue_data.get("html_url", "")
            }
            
            log(f"Title command detected from {cmd['author']}: {title}")
            execute_screenshot_command(cmd)
            
            # 処理完了をマーク
            PROCESSING_TITLE_HASH = None
                
        return True
        
    except Exception as e:
        log(f"Error checking title: {e}")
        return False

def check_new_commands():
    """新しいコメントでスクリーンショット指示をチェック"""
    try:
        owner, repo = GITHUB_REPO.split("/", 1)
        url = f"{API_BASE}/repos/{owner}/{repo}/issues/{MONITOR_ISSUE}/comments"
        
        # since パラメータで最後のコメントID以降のみ取得
        last_id = get_last_comment_id()
        params = {"since": f"2020-01-01T00:00:00Z"}  # 全部取得してからフィルタ
        
        r = SESSION.get(url, params=params, timeout=30)
        if r.status_code != 200:
            log(f"GitHub API error: {r.status_code} {r.text}")
            return False
            
        comments = r.json()
        new_commands = []
        
        for comment in comments:
            comment_id = comment["id"]
            if comment_id <= last_id:
                continue
                
            body = comment.get("body", "").strip().lower()
            author = comment.get("user", {}).get("login", "unknown")
            created_at = comment.get("created_at", "")
            
            # スクリーンショット指示を検知（「ss」のみ、自分のリプライは除外）
            if "ss" in body and not body.startswith("screenshot taken"):
                new_commands.append({
                    "id": comment_id,
                    "author": author,
                    "body": body,
                    "created_at": created_at,
                    "url": comment.get("html_url", "")
                })
                
        if new_commands:
            # 最新のコメントIDを保存
            latest_id = max(cmd["id"] for cmd in new_commands)
            save_last_comment_id(latest_id)
            
            for cmd in new_commands:
                log(f"Screenshot command detected from {cmd['author']}: {cmd['body']}")
                execute_screenshot_command(cmd)
                
        return True
        
    except Exception as e:
        log(f"Error checking commands: {e}")
        return False

def capture_png_bytes():
    """スクリーンショット撮影"""
    shot = pyautogui.screenshot()
    buf = io.BytesIO()
    shot.save(buf, format="PNG")
    return buf.getvalue()

def github_put_file(path_in_repo: str, content_bytes: bytes, message: str):
    """GitHub にファイルをアップロード"""
    owner, repo = GITHUB_REPO.split("/", 1)
    url = f"{API_BASE}/repos/{owner}/{repo}/contents/{path_in_repo}"
    b64 = base64.b64encode(content_bytes).decode("ascii")
    payload = {
        "message": message,
        "content": b64,
        "branch": GITHUB_BRANCH,
    }
    r = SESSION.put(url, json=payload, timeout=60)
    if r.status_code not in (200, 201):
        raise Exception(f"Upload failed: {r.status_code} {r.text}")
    return r.json().get("content", {}).get("html_url")

def post_reply_comment(original_cmd, screenshot_url):
    """実行結果をリプライとして投稿"""
    owner, repo = GITHUB_REPO.split("/", 1)
    url = f"{API_BASE}/repos/{owner}/{repo}/issues/{MONITOR_ISSUE}/comments"
    
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    body = f"""✅ **Screenshot taken** (requested by @{original_cmd['author']})

📸 **File**: {screenshot_url}
🕒 **Time**: {ts}
💻 **Host**: {socket.gethostname()}

![screenshot]({screenshot_url}?raw=1)

*Auto-captured in response to: {original_cmd['url']}*"""

    r = SESSION.post(url, json={"body": body}, timeout=30)
    if r.status_code not in (200, 201):
        log(f"Reply comment failed: {r.status_code} {r.text}")
    else:
        log("Reply comment posted successfully")

def execute_screenshot_command(cmd):
    """スクリーンショット指示を実行"""
    try:
        log(f"Executing screenshot command from {cmd['author']}")
        
        # スクリーンショット撮影
        png_data = capture_png_bytes()
        size_kb = len(png_data) // 1024
        
        log(f"Screenshot captured: {size_kb}KB")
        
        # ファイル名生成
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        host = socket.gethostname()
        rel_path = f"screenshots/{datetime.now().strftime('%Y/%m')}/{ts}_{host}_remote.png"
        
        # GitHubにアップロード
        try:
            commit_msg = f"Remote screenshot {ts} (requested by {cmd['author']})"
            screenshot_url = github_put_file(rel_path, png_data, commit_msg)
            
            log(f"Screenshot uploaded: {screenshot_url}")
            
            # 結果をリプライコメントで報告（アップロード成功版）
            post_reply_comment(cmd, screenshot_url)
            
        except Exception as upload_error:
            log(f"Upload failed: {upload_error}")
            
            # アップロード失敗時はローカル情報のみ報告
            ts_display = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            owner, repo = GITHUB_REPO.split("/", 1)
            url = f"{API_BASE}/repos/{owner}/{repo}/issues/{MONITOR_ISSUE}/comments"
            
            body = f"Screenshot taken (requested by @{cmd['author']})\\n\\nTime: {ts_display}\\nHost: {host}\\nSize: {size_kb}KB\\n\\nNote: Upload failed - {str(upload_error)}"
            
            r = SESSION.post(url, json={"body": body}, timeout=30)
            if r.status_code in (200, 201):
                log("Reply comment posted successfully (upload failed)")
            else:
                log(f"Reply comment failed: {r.status_code} {r.text}")
        
    except Exception as e:
        log(f"Failed to execute screenshot: {e}")
        # エラーも報告
        try:
            error_body = f"Screenshot failed: {str(e)}\\n\\nRequested by @{cmd['author']}"
            owner, repo = GITHUB_REPO.split("/", 1)
            url = f"{API_BASE}/repos/{owner}/{repo}/issues/{MONITOR_ISSUE}/comments"
            SESSION.post(url, json={"body": error_body}, timeout=30)
        except:
            pass

def monitor_loop():
    """メイン監視ループ"""
    _assert_config()
    log(f"Starting remote screenshot monitor (Issue #{MONITOR_ISSUE})")
    log(f"Poll interval: {POLL_INTERVAL} seconds")
    
    try:
        while True:
            # コメントとタイトル両方をチェック
            check_new_commands()
            check_issue_title()
            time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        log("Monitor stopped by user")
    except Exception as e:
        log(f"Monitor crashed: {e}")
        time.sleep(60)  # 1分待ってから再起動を試行

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="Check once and exit")
    parser.add_argument("--test", action="store_true", help="Test screenshot upload")
    args = parser.parse_args()
    
    _assert_config()
    
    if args.test:
        log("Test screenshot...")
        fake_cmd = {
            "id": 999999,
            "author": "test",
            "body": "test screenshot",
            "created_at": datetime.now().isoformat(),
            "url": "https://github.com/test"
        }
        execute_screenshot_command(fake_cmd)
        return
    
    if args.once:
        check_new_commands()
        return
        
    monitor_loop()

if __name__ == "__main__":
    main()