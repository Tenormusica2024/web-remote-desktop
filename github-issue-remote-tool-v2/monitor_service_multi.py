#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Issue Remote Control Monitor Service (v2 - Multi-Issue)
複数Issue同時監視・ウィンドウ直接操作方式
"""

import requests
import time
import json
import logging
from pathlib import Path
from datetime import datetime
import pyautogui
import pyperclip
import pygetwindow as gw
from PIL import ImageGrab
import re
from urllib.parse import urlparse

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("monitor_service.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

class IssueTracker:
    """個別Issue追跡クラス"""
    def __init__(self, url, token):
        self.url = url
        self.token = token
        self.parse_url()
        
        self.state_file = Path(f".monitor_state_{self.repo.replace('/', '_')}_issue{self.issue_num}.json")
        self.last_comment_id = None
        self.load_state()
    
    def parse_url(self):
        """Issue URLをパース（省略形式・スペース区切りも対応）"""
        url = self.url.replace(" ", "")
        
        if url.startswith("ttps://"):
            url = "h" + url
        
        match = re.match(r'https://github\.com/([^/]+)/([^/]+)/issues/(\d+)', url)
        if not match:
            raise ValueError(f"無効なIssue URL: {self.url}")
        
        owner, repo_name, issue_num = match.groups()
        self.owner = owner
        self.repo_name = repo_name
        self.repo = f"{owner}/{repo_name}"
        self.issue_num = issue_num
        self.full_url = url
    
    def load_state(self):
        """状態ファイル読み込み"""
        if self.state_file.exists():
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    state = json.load(f)
                self.last_comment_id = state.get("last_comment_id")
                logging.info(f"✅ [{self.repo} #{self.issue_num}] 状態読み込み: last_comment_id={self.last_comment_id}")
            except Exception as e:
                logging.warning(f"⚠️ [{self.repo} #{self.issue_num}] 状態読み込み失敗: {e}")
    
    def save_state(self):
        """状態ファイル保存"""
        try:
            state = {
                "last_comment_id": self.last_comment_id,
                "url": self.url,
                "repo": self.repo,
                "issue_number": self.issue_num,
                "updated_at": datetime.now().isoformat()
            }
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"❌ [{self.repo} #{self.issue_num}] 状態保存エラー: {e}")
    
    def get_comments(self):
        """コメント取得"""
        try:
            url = f"https://api.github.com/repos/{self.repo}/issues/{self.issue_num}/comments"
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github.v3+json"
            }
            params = {"per_page": 100, "sort": "created", "direction": "asc"}
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            return response.json()
        except Exception as e:
            logging.error(f"❌ [{self.repo} #{self.issue_num}] GitHub API接続エラー: {e}")
            return []
    
    def get_new_comments(self):
        """新規コメント取得"""
        comments = self.get_comments()
        if not comments:
            return []
        
        new_comments = []
        for comment in comments:
            comment_id = comment["id"]
            if self.last_comment_id is None or comment_id > self.last_comment_id:
                new_comments.append(comment)
                self.last_comment_id = comment_id
        
        if new_comments:
            self.save_state()
        
        return new_comments
    
    def post_comment(self, body):
        """コメント投稿"""
        try:
            url = f"https://api.github.com/repos/{self.repo}/issues/{self.issue_num}/comments"
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            response = requests.post(url, json={"body": body}, headers=headers, timeout=30)
            response.raise_for_status()
            
            return True
        except Exception as e:
            logging.error(f"❌ [{self.repo} #{self.issue_num}] コメント投稿エラー: {e}")
            return False

class GitHubIssueMonitor:
    def __init__(self):
        self.config_file = Path("config.json")
        
        self.gh_token = None
        self.issues = []
        self.poll_interval = 5
        
        self.claude_windows = []
        
        self.load_config()
    
    def load_config(self):
        """設定ファイル読み込み"""
        if not self.config_file.exists():
            logging.error(f"❌ 初期化エラー: {self.config_file} が見つかりません")
            logging.error("解決方法: python setup_wizard.py を実行してください")
            raise FileNotFoundError(f"{self.config_file} が見つかりません")
        
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            self.gh_token = config.get("github_token")
            issue_configs = config.get("issues", [])
            self.poll_interval = config.get("poll_interval", 5)
            
            if not self.gh_token:
                raise ValueError("GitHub tokenが設定されていません")
            
            if not issue_configs:
                raise ValueError("監視するIssueが設定されていません")
            
            for issue_config in issue_configs:
                if issue_config.get("enabled", True):
                    url = issue_config.get("url")
                    if url:
                        try:
                            tracker = IssueTracker(url, self.gh_token)
                            self.issues.append(tracker)
                            logging.info(f"✅ Issue登録: {tracker.repo} #{tracker.issue_num}")
                        except Exception as e:
                            logging.error(f"❌ Issue登録失敗 ({url}): {e}")
            
            if not self.issues:
                raise ValueError("有効なIssueが1つも登録されていません")
            
            logging.info(f"✅ 設定ファイル読み込み完了: {len(self.issues)}個のIssueを監視")
            
        except Exception as e:
            logging.error(f"❌ 設定ファイル読み込みエラー: {e}")
            raise
    
    def detect_claude_windows(self):
        """Claude Codeウィンドウを検出"""
        all_windows = gw.getAllWindows()
        claude_windows = []
        
        for window in all_windows:
            title = window.title.lower()
            if "claude" in title and window.visible:
                claude_windows.append(window)
        
        self.claude_windows = claude_windows
        return len(claude_windows)
    
    def send_text_to_window(self, window, text):
        """Claude Codeウィンドウにテキスト送信"""
        methods = [
            self._send_method1,
            self._send_method3,
        ]
        
        for i, method in enumerate(methods, 1):
            try:
                if method(window, text):
                    logging.info(f"✅ テキスト送信成功（方法{i}）")
                    return True
            except Exception as e:
                logging.warning(f"⚠️ 方法{i}失敗: {e}")
        
        logging.error("❌ すべての送信方法が失敗しました")
        return False
    
    def _send_method1(self, window, text):
        """方法1: ウィンドウアクティブ化 + Ctrl+V"""
        if window.isMinimized:
            window.restore()
        window.activate()
        time.sleep(0.3)
        
        old_clip = pyperclip.paste()
        pyperclip.copy(text)
        time.sleep(0.1)
        
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.2)
        pyautogui.press("enter")
        time.sleep(0.1)
        
        pyperclip.copy(old_clip)
        return True
    
    def _send_method3(self, window, text):
        """方法3: ウィンドウ中央下部クリック + Ctrl+V"""
        if window.isMinimized:
            window.restore()
        window.activate()
        time.sleep(0.3)
        
        center_x = window.left + window.width // 2
        center_y = window.top + int(window.height * 0.9)
        
        pyautogui.click(center_x, center_y)
        time.sleep(0.2)
        
        old_clip = pyperclip.paste()
        pyperclip.copy(text)
        time.sleep(0.1)
        
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.2)
        pyautogui.press("enter")
        time.sleep(0.1)
        
        pyperclip.copy(old_clip)
        return True
    
    def process_comment(self, comment, issue_tracker):
        """個別コメント処理"""
        comment_id = comment["id"]
        author = comment["user"]["login"]
        body = comment["body"].strip()
        
        logging.info(f"📝 [{issue_tracker.repo} #{issue_tracker.issue_num}] コメント#{comment_id} by @{author}")
        
        if body.startswith("📸") or body.startswith("**Screenshot**") or body.startswith("🤖"):
            logging.info("⏭️ システムコメントをスキップ")
            return
        
        if body == "ss":
            logging.info("📸 スクリーンショット要求を検出")
            self.take_and_upload_screenshot(issue_tracker)
            return
        
        target_window = None
        actual_text = body
        
        for i in range(1, 10):
            prefix = f"#{i}:"
            if body.startswith(prefix):
                actual_text = body[len(prefix):].strip()
                num_windows = self.detect_claude_windows()
                
                if num_windows == 0:
                    logging.error(f"❌ Claude Codeウィンドウが見つかりません")
                    return
                
                if i > num_windows:
                    logging.error(f"❌ Claude Code #{i} が存在しません（検出数: {num_windows}）")
                    return
                
                target_window = self.claude_windows[i - 1]
                logging.info(f"🎯 転送先: Claude Code #{i} ({target_window.title})")
                break
        
        if target_window is None:
            num_windows = self.detect_claude_windows()
            if num_windows == 0:
                logging.error(f"❌ Claude Codeウィンドウが見つかりません")
                return
            target_window = self.claude_windows[0]
            logging.info(f"🎯 転送先: デフォルト（Claude Code #1: {target_window.title}）")
        
        logging.info(f"📤 [{issue_tracker.repo} #{issue_tracker.issue_num}] 転送開始: {actual_text[:50]}...")
        success = self.send_text_to_window(target_window, actual_text)
        
        if success:
            logging.info(f"✅ 転送成功")
        else:
            logging.error(f"❌ 転送失敗")
    
    def take_and_upload_screenshot(self, issue_tracker):
        """スクリーンショット撮影・アップロード"""
        try:
            logging.info(f"📸 [{issue_tracker.repo} #{issue_tracker.issue_num}] スクリーンショット撮影開始")
            
            screenshot = ImageGrab.grab()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            
            screenshot.save(filename)
            logging.info(f"✅ スクリーンショット保存: {filename}")
            
            self.upload_to_github(filename, issue_tracker)
            
        except Exception as e:
            logging.error(f"❌ スクリーンショット処理エラー: {e}")
    
    def upload_to_github(self, filepath, issue_tracker):
        """GitHub Issueに画像アップロード"""
        try:
            import base64
            
            upload_url = f"https://api.github.com/repos/{issue_tracker.repo}/contents/{filepath}"
            
            with open(filepath, "rb") as f:
                content = base64.b64encode(f.read()).decode()
            
            upload_data = {
                "message": f"Add screenshot {filepath}",
                "content": content
            }
            
            upload_headers = {
                "Authorization": f"Bearer {self.gh_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            upload_response = requests.put(upload_url, headers=upload_headers, json=upload_data, timeout=30)
            
            if upload_response.status_code in [200, 201]:
                file_data = upload_response.json()
                download_url = file_data.get("content", {}).get("download_url")
                
                comment_body = f"📸 **Screenshot** `{filepath}`\n\n![Screenshot]({download_url})"
                
                issue_tracker.post_comment(comment_body)
                
                logging.info(f"✅ スクリーンショットアップロード完了")
            else:
                logging.error(f"❌ ファイルアップロード失敗: {upload_response.status_code}")
            
        except Exception as e:
            logging.error(f"❌ GitHub アップロードエラー: {e}")
    
    def run(self):
        """監視サービス実行"""
        logging.info("=" * 60)
        logging.info("GitHub Issue Remote Control Monitor Service (v2 - Multi)")
        logging.info("=" * 60)
        logging.info(f"監視Issue数: {len(self.issues)}")
        for issue in self.issues:
            logging.info(f"  - {issue.repo} #{issue.issue_num} ({issue.url})")
        logging.info(f"Poll interval: {self.poll_interval}秒")
        logging.info("=" * 60)
        
        num_windows = self.detect_claude_windows()
        if num_windows > 0:
            logging.info(f"✅ Claude Codeウィンドウを{num_windows}個検出")
            for i, window in enumerate(self.claude_windows, 1):
                logging.info(f"  #{i}: {window.title}")
        else:
            logging.warning("⚠️ Claude Codeウィンドウが見つかりません（起動後に自動検出します）")
        
        logging.info("🚀 Issue監視開始...")
        
        try:
            while True:
                for issue_tracker in self.issues:
                    new_comments = issue_tracker.get_new_comments()
                    if new_comments:
                        logging.info(f"📬 [{issue_tracker.repo} #{issue_tracker.issue_num}] 新規コメント {len(new_comments)}件")
                        for comment in new_comments:
                            self.process_comment(comment, issue_tracker)
                
                time.sleep(self.poll_interval)
        except KeyboardInterrupt:
            logging.info("\n⏹️ 監視サービスを停止します")
        except Exception as e:
            logging.error(f"❌ 予期しないエラー: {e}")
            raise

def main():
    try:
        monitor = GitHubIssueMonitor()
        monitor.run()
    except Exception as e:
        logging.error(f"❌ 起動失敗: {e}")
        input("\nエラーが発生しました。Enterキーで終了します...")

if __name__ == "__main__":
    main()