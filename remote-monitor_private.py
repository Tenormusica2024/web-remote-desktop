#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Remote Screenshot Monitor via GitHub Issues - PRIVATE REPOSITORY VERSION
- 社内PCからGitHub Issueに「screenshot」コメント → 自宅PCが検知して自動撮影
- バックグラウンド監視サービス（常駐型）
- Private repository support with enhanced authentication
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

# ---------- Config - Private Repository Version ----------
ROOT = Path(__file__).resolve().parent
# Load private repository configuration first
load_dotenv(ROOT / ".env_private", override=True)
# Fallback to standard .env if private config not found
if not os.getenv("GITHUB_TOKEN"):
    load_dotenv(ROOT / ".env", override=True)

# 環境変数から設定を読み込み
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO", "Tenormusica2024/web-remote-desktop")
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "master")
MONITOR_ISSUE = os.getenv("MONITOR_ISSUE_NUMBER", "1")  # 監視対象Issue番号
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "30"))  # 秒

API_BASE = "https://api.github.com"
LAST_COMMENT_FILE = ROOT / "last_comment_id_private.txt"
LAST_TITLE_FILE = ROOT / "last_title_content_private.txt"
LOG_FILE = ROOT / "monitor_private.log"

# グローバル変数：処理中のタイトルを追跡
PROCESSING_TITLE_HASH = None

SESSION = requests.Session()
SESSION.headers.update({
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "claude-code-private-title-monitor/1.0"
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
        
        # タイトルでスクリーンショット指示を検知（「ss」を含む）
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
                
            # 処理開始をマーク（重複実行を厳格に防ぐ）
            PROCESSING_TITLE_HASH = current_title_content
            
            # 新しいタイトル内容を保存（実行前に保存して重複防止）
            try:
                LAST_TITLE_FILE.write_text(current_title_content, encoding='utf-8')
                log(f"Processing new title command: {current_title_content}")
            except Exception as e:
                log(f"Error saving title content: {e}")
                # 処理完了をマーク（エラー時も解除）
                PROCESSING_TITLE_HASH = None
                return False
                
            # コマンド実行
            cmd = {
                "id": f"title_{updated_at}_{int(time.time())}",  # タイムスタンプで一意性確保
                "author": author,
                "body": f"Title command: {title}",
                "created_at": updated_at,
                "url": issue_data.get("html_url", "")
            }
            
            log(f"Executing single title command from {cmd['author']}: {title}")
            execute_screenshot_command(cmd)
            
            # 処理完了をマーク
            PROCESSING_TITLE_HASH = None
                
        return True
        
    except Exception as e:
        log(f"Error checking title: {e}")
        return False

def check_new_commands():
    """新しいコメントでスクリーンショット指示をチェック（重複防止強化）"""
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
            
            # デバッグ: すべてのコメントをログ記録
            log(f"DEBUG: Checking comment ID {comment_id} from {author}: '{body[:50]}{'...' if len(body) > 50 else ''}'")
            
            # スクリーンショット指示を検知（「ss」を含む）
            # 1. 「ss」を含む
            # 2. 自分のリプライではない（"screenshot taken"で始まらない）
            # 3. システムコメントではない（"Generated with Claude Code"を含まない）
            if ("ss" in body and 
                not body.startswith("screenshot taken") and 
                "generated with claude code" not in body and
                "auto-captured in response" not in body):
                
                log(f"DEBUG: Valid 'ss' command detected from {author}: '{body}'")
                new_commands.append({
                    "id": comment_id,
                    "author": author,
                    "body": body,
                    "created_at": created_at,
                    "url": comment.get("html_url", "")
                })
                
        if new_commands:
            # 重複チェック：同じ作者の連続したコメントは1つだけ処理
            filtered_commands = []
            last_author = None
            last_body = None
            
            for cmd in sorted(new_commands, key=lambda x: x["created_at"]):
                # 同じ作者で同じ内容のコメントをスキップ
                if cmd["author"] == last_author and cmd["body"] == last_body:
                    log(f"Skipping duplicate command from {cmd['author']}: {cmd['body']}")
                    continue
                    
                filtered_commands.append(cmd)
                last_author = cmd["author"]
                last_body = cmd["body"]
            
            if filtered_commands:
                # 最新のコメントIDを保存
                latest_id = max(cmd["id"] for cmd in new_commands)
                save_last_comment_id(latest_id)
                
                # 実際に処理するコマンドは1つだけ（最新）
                cmd = filtered_commands[-1]
                log(f"Processing single screenshot command from {cmd['author']}: {cmd['body']}")
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
    """メイン監視ループ（重複防止強化 + 10時間制限）"""
    _assert_config()
    
    # 10時間 = 36000秒の制限
    start_time = time.time()
    max_duration = 10 * 60 * 60  # 10 hours in seconds
    
    log(f"Starting remote screenshot monitor (Issue #{MONITOR_ISSUE})")
    log(f"Poll interval: {POLL_INTERVAL} seconds")
    log(f"Duplicate prevention: ENABLED")
    log(f"Auto-stop after: 10 hours (36000 seconds)")
    log(f"Monitor will automatically stop at: {datetime.fromtimestamp(start_time + max_duration).strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        while True:
            # 10時間制限をチェック
            elapsed = time.time() - start_time
            if elapsed >= max_duration:
                log(f"Auto-stopping after {elapsed/3600:.1f} hours of operation")
                break
            
            # 1時間ごとに残り時間をログ出力
            if int(elapsed) % 3600 == 0 and int(elapsed) > 0:
                remaining_hours = (max_duration - elapsed) / 3600
                log(f"Monitor running: {elapsed/3600:.1f}h elapsed, {remaining_hours:.1f}h remaining")
            
            # コメントとタイトル両方をチェック（順次実行で重複を防ぐ）
            check_new_commands()
            time.sleep(2)  # 小さな間隔でコメントとタイトル処理を分離
            check_issue_title()
            time.sleep(POLL_INTERVAL)
            
    except KeyboardInterrupt:
        elapsed = time.time() - start_time
        log(f"Monitor stopped by user after {elapsed/3600:.1f} hours")
    except Exception as e:
        elapsed = time.time() - start_time
        log(f"Monitor crashed after {elapsed/3600:.1f} hours: {e}")
        time.sleep(60)  # 1分待ってから再起動を試行
    
    log("Monitor shutdown complete")

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