#!/usr/bin/env python3
"""
GitHub Issue #5 Monitor SubAgent
Claude Codeの応答漏れを検出して自動報告する外部監視プロセス

動作:
1. GitHub Issue #5の最新コメントを定期監視
2. Claude Code宛のメッセージ検出
3. 一定時間応答なしで自動報告実行
"""

import os
import time
import json
import subprocess
import datetime
from pathlib import Path
import sys

# 設定
GITHUB_OWNER = "Tenormusica2024"
GITHUB_REPO = "Private"
ISSUE_NUMBER = 5
CHECK_INTERVAL = 30  # 30秒ごとにチェック
WAIT_THRESHOLD = 120  # 2分応答なしで自動報告
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

# ログファイル
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "monitor-subagent.log"

# 状態管理ファイル
STATE_FILE = Path(__file__).parent / ".monitor_state.json"
REPORT_SCRIPT = Path(__file__).parent / "task_complete_private.py"
AUTO_REPORT_HISTORY = Path(__file__).parent / ".auto_report_history.json"
PENDING_MESSAGE_FILE = Path(__file__).parent / "pending_claude_message.txt"


def log(message):
    """ログ出力"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    print(log_entry)
    
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry + "\n")


def load_state():
    """状態ファイルの読み込み"""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {
        "last_claude_message_id": None,
        "pending_response": None,
        "monitor_started": datetime.datetime.now().isoformat(),
        "auto_reported_ids": []  # 自動報告済みのメッセージIDリスト
    }


def save_state(state):
    """状態ファイルの保存"""
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def get_issue_comments():
    """GitHub Issue #5のコメントを取得"""
    try:
        # PowerShellラッパー経由でGitHub CLIを実行
        wrapper_path = Path(__file__).parent / "github-issue-monitor-wrapper.ps1"
        cmd = [
            "powershell", "-ExecutionPolicy", "Bypass", "-File",
            str(wrapper_path), "-Action", "get-comments"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, encoding='utf-8')
        
        if result.returncode == 0 and result.stdout:
            # "Claude Auto-Mode loaded" の行を除外してJSONをパース
            output_lines = result.stdout.strip().split('\n')
            json_lines = [line for line in output_lines if not line.startswith('Claude Auto-Mode')]
            json_str = '\n'.join(json_lines)
            
            if json_str:
                comments = json.loads(json_str)
                return comments
            else:
                log("JSONデータが見つかりません")
                return []
        else:
            if result.stderr:
                log(f"GitHub API エラー: {result.stderr}")
            return []
            
    except Exception as e:
        log(f"コメント取得エラー: {e}")
        return []


def is_claude_message(comment):
    """Claude Code宛のメッセージか判定"""
    body = comment.get("body", "")
    
    # Claude Code宛のマーカー
    markers = [
        "🚨🚨🚨 MANDATORY",
        "このメッセージはGitHub Issueから来ています",
        "upper:",
        "lower:"
    ]
    
    return any(marker in body for marker in markers)


def is_claude_response(comment, pending_message_id=None, pending_created_at=None):
    """Claude Codeからの応答か判定（時系列チェック付き）"""
    body = comment.get("body", "")
    
    # Claude Code応答のマーカー
    markers = [
        "Claude Code Task Report System",
        "実行者**: Claude Code",
        "Generated with [Claude Code]"
    ]
    
    # マーカーが含まれているか
    has_marker = any(marker in body for marker in markers)
    
    if not has_marker:
        return False
    
    # 時系列チェック：pending_created_atより新しいコメントのみ応答として認識
    if pending_created_at:
        comment_time = datetime.datetime.fromisoformat(comment['created_at'].replace('Z', '+00:00'))
        pending_time = datetime.datetime.fromisoformat(pending_created_at.replace('Z', '+00:00'))
        
        # pendingメッセージより古いコメントは応答として認識しない
        if comment_time <= pending_time:
            log(f"  古い応答をスキップ: comment_id={comment['id']}, time={comment['created_at']}")
            return False
        
        log(f"  新しい応答を検出: comment_id={comment['id']}, time={comment['created_at']}")
    
    return True


def auto_report(pending_message, state):
    """応答漏れを自動報告（重複防止付き）"""
    message_id = pending_message['id']
    
    # 既に報告済みかチェック
    if 'auto_reported_ids' not in state:
        state['auto_reported_ids'] = []
    
    if message_id in state['auto_reported_ids']:
        log(f"メッセージID={message_id}は既に自動報告済み、スキップ")
        return False
    
    log(f"応答漏れ検出！自動報告を実行します（ID={message_id}）")
    
    # 未送信メッセージファイルを読み込み
    pending_claude_message = ""
    if PENDING_MESSAGE_FILE.exists():
        try:
            with open(PENDING_MESSAGE_FILE, "r", encoding="utf-8") as f:
                pending_claude_message = f.read().strip()
                log(f"未送信メッセージを検出: {len(pending_claude_message)}文字")
        except Exception as e:
            log(f"未送信メッセージ読み込みエラー: {e}")
    
    # Claude Codeの未送信メッセージセクション
    claude_message_section = ""
    if pending_claude_message:
        claude_message_section = f"""
### Claude Codeが送信しようとしていた内容

{pending_claude_message}

---
"""
    
    report_message = f"""## GitHub Issue Monitor SubAgent - 自動報告

**応答漏れ検出**

Claude Codeが以下のメッセージに応答していません：

### 未応答メッセージ
- **ID**: {pending_message['id']}
- **送信者**: {pending_message['user']}
- **送信時刻**: {pending_message['created_at']}
- **経過時間**: {pending_message['elapsed_minutes']:.1f}分
{claude_message_section}
### 自動報告
この報告は外部監視サブエージェントにより自動生成されました。
Claude Codeからの応答が{WAIT_THRESHOLD}秒以上ありません。

---
⏰ **報告時刻**: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🤖 **実行者**: GitHub Issue Monitor SubAgent
"""
    
    try:
        # task_complete_private.py を実行
        result = subprocess.run(
            ["python", str(REPORT_SCRIPT), report_message],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            log("自動報告成功")
            # 報告済みリストに追加
            if 'auto_reported_ids' not in state:
                state['auto_reported_ids'] = []
            state['auto_reported_ids'].append(message_id)
            save_state(state)
            
            # 未送信メッセージファイルをクリア
            if PENDING_MESSAGE_FILE.exists():
                try:
                    PENDING_MESSAGE_FILE.unlink()
                    log("未送信メッセージファイルをクリア")
                except:
                    pass
            
            return True
        else:
            log(f"自動報告失敗: {result.stderr}")
            return False
            
    except Exception as e:
        log(f"自動報告エラー: {e}")
        return False


def monitor_loop():
    """メイン監視ループ"""
    log("GitHub Issue #5 監視サブエージェント起動")
    state = load_state()
    
    while True:
        try:
            # GitHub Issueのコメントを取得
            comments = get_issue_comments()
            
            if not comments:
                log("コメント取得失敗、次回チェックまで待機")
                time.sleep(CHECK_INTERVAL)
                continue
            
            # 最新のコメントから順にチェック
            comments_sorted = sorted(comments, key=lambda x: x['created_at'], reverse=True)
            
            log(f"コメント数: {len(comments)}件")
            
            for comment in comments_sorted:
                comment_id = comment['id']
                
                # Claude Code宛のメッセージを検出
                if is_claude_message(comment):
                    # 既知のメッセージはスキップ
                    if state["last_claude_message_id"] == comment_id:
                        break
                    
                    # 新しいClaude Code宛メッセージ
                    created_at = datetime.datetime.fromisoformat(comment['created_at'].replace('Z', '+00:00'))
                    elapsed = (datetime.datetime.now(datetime.timezone.utc) - created_at).total_seconds()
                    
                    # 古すぎるメッセージはスキップ（1時間以上前）
                    if elapsed > 3600:  # 1時間 = 3600秒
                        log(f"  古すぎるメッセージをスキップ: ID={comment_id}, 経過={elapsed/60:.1f}分")
                        state["last_claude_message_id"] = comment_id  # 既読として記録
                        save_state(state)
                        continue
                    
                    log(f"Claude Code宛メッセージ検出: ID={comment_id}, 経過={elapsed:.0f}秒")
                    log(f"  送信者: {comment['user']['login']}, 時刻: {comment['created_at']}")
                    
                    # 応答待ちとして記録
                    state["pending_response"] = {
                        "id": comment_id,
                        "user": comment['user']['login'],
                        "created_at": comment['created_at'],
                        "elapsed_minutes": elapsed / 60
                    }
                    state["last_claude_message_id"] = comment_id
                    save_state(state)
                    
                # Claude Codeからの応答を検出
                elif state["pending_response"] and is_claude_response(
                    comment, 
                    pending_message_id=state["pending_response"].get("id"),
                    pending_created_at=state["pending_response"].get("created_at")
                ):
                    log(f"Claude Code応答検出（ID={comment['id']}）、応答待ちクリア")
                    state["pending_response"] = None
                    save_state(state)
                    break
            
            # 応答待ちチェック
            if state["pending_response"]:
                created_at = datetime.datetime.fromisoformat(state["pending_response"]["created_at"].replace('Z', '+00:00'))
                elapsed = (datetime.datetime.now(datetime.timezone.utc) - created_at).total_seconds()
                state["pending_response"]["elapsed_minutes"] = elapsed / 60
                
                if elapsed >= WAIT_THRESHOLD:
                    log(f"応答タイムアウト！{elapsed:.0f}秒経過")
                    
                    # 自動報告実行（重複防止付き）
                    if auto_report(state["pending_response"], state):
                        # 報告成功したら応答待ちクリア
                        state["pending_response"] = None
                        save_state(state)
                else:
                    log(f"応答待機中... {elapsed:.0f}/{WAIT_THRESHOLD}秒")
            
        except Exception as e:
            log(f"監視ループエラー: {e}")
        
        # 次回チェックまで待機
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    try:
        monitor_loop()
    except KeyboardInterrupt:
        log("監視サブエージェント停止")
        sys.exit(0)