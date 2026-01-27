#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Issue #5 Monitor SubAgent
Claude Codeの応答漏れを検出して自動報告する外部監視プロセス

動作:
1. GitHub Issue #5の最新コメントを定期監視
2. Claude Code宛のメッセージ検出
3. 一定時間応答なしで自動報告実行
"""

import os
import sys
import io
import time
import json
import subprocess
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Windows環境でのUTF-8出力を確実にする
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='ignore')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='ignore')

# 設定ファイルを読み込む
CONFIG_FILE = Path(__file__).parent / "config.json"

def load_config() -> Dict[str, Any]:
    """設定ファイルを読み込む（デフォルト値付き）"""
    default_config = {
        "monitoring": {
            "check_interval_seconds": 30,
            "wait_threshold_seconds": 120,
            "max_auto_reported_ids": 10,
            "old_message_threshold_hours": 1
        },
        "github": {
            "owner": "Tenormusica2024",
            "repo": "Private",
            "issue_number": 5
        },
        "logging": {
            "enable_debug": True,
            "log_api_responses": False,
            "log_detailed_timing": True
        },
        "performance": {
            "enable_comment_caching": True,
            "max_comment_history": 50
        }
    }
    
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                # デフォルト設定をマージ
                for section, values in default_config.items():
                    if section not in config:
                        config[section] = values
                    else:
                        for key, default_value in values.items():
                            if key not in config[section]:
                                config[section][key] = default_value
                return config
        except Exception as e:
            log(f"設定ファイル読み込みエラー（デフォルト値使用）: {e}")
    
    return default_config

# 設定をロード
config = load_config()
GITHUB_OWNER = config["github"]["owner"]
GITHUB_REPO = config["github"]["repo"]
ISSUE_NUMBER = config["github"]["issue_number"]
CHECK_INTERVAL = config["monitoring"]["check_interval_seconds"]
WAIT_THRESHOLD = config["monitoring"]["wait_threshold_seconds"]
MAX_AUTO_REPORTED_IDS = config["monitoring"]["max_auto_reported_ids"]
OLD_MESSAGE_THRESHOLD_HOURS = config["monitoring"]["old_message_threshold_hours"]
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


def log(message: str, level: str = "INFO") -> None:
    """詳細ログ出力（レベル・実行時間付き）"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    log_entry = f"[{timestamp}] [{level:5s}] {message}"
    print(log_entry)
    
    try:
        with open(LOG_FILE, "a", encoding="utf-8", errors="ignore") as f:
            f.write(log_entry + "\n")
    except Exception as e:
        print(f"ログ書き込みエラー: {e}")

def debug_log(message: str) -> None:
    """デバッグログ（設定で無効化可能）"""
    if config["logging"]["enable_debug"]:
        log(message, "DEBUG")

def error_log(message: str) -> None:
    """エラーログ"""
    log(message, "ERROR")


def load_state() -> Dict[str, Any]:
    """
    状態ファイルの読み込み
    
    Returns:
        Dict[str, Any]: サブエージェントの状態情報
            - last_claude_message_id: 最後に処理したClaude Code宛メッセージID
            - pending_response: 現在応答待ちのメッセージ情報
            - monitor_started: 監視開始時刻
            - auto_reported_ids: 自動報告済みメッセージIDリスト
    """
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                state_data = json.load(f)
                # auto_reported_ids が設定上限を超えたら古いものから削除
                max_ids = config["monitoring"]["max_auto_reported_ids"]
                if "auto_reported_ids" in state_data and len(state_data["auto_reported_ids"]) > max_ids:
                    state_data["auto_reported_ids"] = state_data["auto_reported_ids"][-max_ids:]
                    log(f"auto_reported_ids を整理（最新{max_ids}件を保持）")
                return state_data
        except json.JSONDecodeError as e:
            error_log(f"状態ファイルJSONパースエラー: {e}")
        except IOError as e:
            error_log(f"状態ファイル読み込みエラー: {e}")
        except Exception as e:
            error_log(f"予期しない状態ファイルエラー: {e}")
    return {
        "last_claude_message_id": None,
        "pending_response": None,
        "monitor_started": datetime.datetime.now().isoformat(),
        "auto_reported_ids": []  # 自動報告済みのメッセージIDリスト
    }


def save_state(state_data: Dict[str, Any]) -> None:
    """
    状態ファイルの保存
    
    Args:
        state_data: 保存する状態データ
    """
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state_data, f, indent=2)
        debug_log(f"状態ファイル保存成功: {STATE_FILE}")
    except Exception as e:
        error_log(f"状態ファイル保存エラー: {e}")


def get_issue_comments() -> List[Dict[str, Any]]:
    """
    GitHub Issue #5のコメントを取得
    
    Returns:
        List[Dict[str, Any]]: コメントリスト（取得失敗時は空リスト）
    """
    try:
        # PowerShellラッパー経由でGitHub CLIを実行
        wrapper_path = Path(__file__).parent / "github-issue-monitor-wrapper.ps1"
        cmd = [
            "powershell", "-ExecutionPolicy", "Bypass", "-File",
            str(wrapper_path), "-Action", "get-comments"
        ]
        
        # Windows環境でPowerShell経由の出力を正しく処理
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, encoding='utf-8', errors='ignore')
        
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
            
            # パフォーマンス最適化: コメント履歴を制限してメモリ節約
            max_history = config["performance"]["max_comment_history"]
            if len(comments) > max_history:
                debug_log(f"コメント履歴を{max_history}件に制限（元: {len(comments)}件）")
                # 最新のコメントのみ保持（created_atでソート後の上位を取得）
                comments = sorted(comments, key=lambda x: x['created_at'], reverse=True)[:max_history]
            else:
                # 通常のソート
                comments = sorted(comments, key=lambda x: x['created_at'], reverse=True)
            
            comments_sorted = comments
            
            log(f"コメント数: {len(comments)}件")
            
            # 新しいClaude Code宛メッセージを最新のものから1つだけ処理
            latest_new_message = None
            
            for comment in comments_sorted:
                comment_id = comment['id']
                
                # Claude Code宛のメッセージを検出
                if is_claude_message(comment):
                    # 既知のメッセージに到達したらループ終了
                    if state["last_claude_message_id"] == comment_id:
                        break
                    
                    # 新しいClaude Code宛メッセージ
                    created_at = datetime.datetime.fromisoformat(comment['created_at'].replace('Z', '+00:00'))
                    elapsed = (datetime.datetime.now(datetime.timezone.utc) - created_at).total_seconds()
                    
                    # 設定可能な古いメッセージ闾値を使用
                    threshold_seconds = config["monitoring"]["old_message_threshold_hours"] * 3600
                    if elapsed > threshold_seconds:
                        debug_log(f"  古すぎるメッセージをスキップ: ID={comment_id}, 経過={elapsed/60:.1f}分")
                        continue
                    
                    if config["logging"]["log_detailed_timing"]:
                        log(f"Claude Code宛メッセージ検出: ID={comment_id}, 経過={elapsed:.0f}秒")
                        debug_log(f"  送信者: {comment['user']['login']}, 時刻: {comment['created_at']}")
                    else:
                        log(f"Claude Code宛メッセージ検出: ID={comment_id}")
                    
                    # 最新の新しいメッセージとして記録（1つだけ）
                    if latest_new_message is None:
                        latest_new_message = {
                            "id": comment_id,
                            "user": comment['user']['login'],
                            "created_at": comment['created_at'],
                            "elapsed_minutes": elapsed / 60
                        }
                    
                    # last_claude_message_idは最新のメッセージIDに更新
                    state["last_claude_message_id"] = comment_id
            
            # 新しいメッセージが見つかった場合、最新の1つだけをpending_responseに設定
            if latest_new_message:
                debug_log(f"  最新メッセージを応答待ちに設定: ID={latest_new_message['id']}")
                state["pending_response"] = latest_new_message
                save_state(state)
            
            # Claude Codeからの応答を検出
            for comment in comments_sorted:
                if is_claude_response(
                    comment, 
                    pending_message_id=state["pending_response"].get("id") if state["pending_response"] else None,
                    pending_created_at=state["pending_response"].get("created_at") if state["pending_response"] else None
                ):
                    # pending_responseがある場合のみクリア
                    if state["pending_response"]:
                        log(f"Claude Code応答検出（ID={comment['id']}）、応答待ちクリア")
                        state["pending_response"] = None
                        save_state(state)
                    else:
                        # pending_responseがない場合は単にClaude応答を検出
                        debug_log(f"Claude Code応答を検出（ID={comment['id']}）")
                    break
            
            # 応答待ちチェック
            if state["pending_response"]:
                created_at = datetime.datetime.fromisoformat(state["pending_response"]["created_at"].replace('Z', '+00:00'))
                elapsed = (datetime.datetime.now(datetime.timezone.utc) - created_at).total_seconds()
                state["pending_response"]["elapsed_minutes"] = elapsed / 60
                
                if elapsed >= WAIT_THRESHOLD:
                    log(f"応答タイムアウト！{elapsed:.0f}秒経過")
                    
                    # 自動報告実行（重複防止付き）
                    auto_report_result = auto_report(state["pending_response"], state)
                    
                    # 報告成功でも既報告でも、応答待ちクリア
                    # （既報告の場合も pending_response を残すと無限ループになる）
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