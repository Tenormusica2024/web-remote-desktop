#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
統合版 GitHub Issue モニター (Unified Monitor)
- マルチリポジトリ対応
- Private/Public両対応
- コマンド転送機能
- スクリーンショット機能
- 常駐サービス機能
- タスク完了報告自動指示

全ての監視機能を一つに統合したオールインワンスクリプト
"""

import os, sys, time, json, logging
import requests
import pyautogui
import pyperclip
import traceback
import io, base64, socket
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Tuple, List

# ============================================================
# 設定クラス
# ============================================================
class UnifiedMonitorConfig:
    """統合監視の設定管理"""
    
    def __init__(self, repo_config: Dict[str, str] = None, use_env: bool = True):
        """
        初期化
        
        Args:
            repo_config: リポジトリ設定 {'owner', 'name', 'issue'}
            use_env: 環境変数/.envファイルを使用するか
        """
        self.root_dir = Path(__file__).resolve().parent
        
        # デフォルト設定
        self.repo_owner = "Tenormusica2024"
        self.repo_name = "Private"
        self.issue_number = 1
        self.poll_interval = 5  # 秒
        self.github_token = None
        
        # 環境変数/.envファイルから読み込み
        if use_env:
            self._load_environment()
        
        # 引数で上書き
        if repo_config:
            self.repo_owner = repo_config.get('owner', self.repo_owner)
            self.repo_name = repo_config.get('name', self.repo_name)
            self.issue_number = repo_config.get('issue', self.issue_number)
            
        # GitHub Token設定
        if not self.github_token:
            self.github_token = self._get_github_token()
            
        # 座標設定
        self.coordinates = self._load_coordinates()
        
        # ファイルパス設定
        self.state_file = self._get_state_file_path()
        
    def _load_environment(self):
        """環境変数/.envファイル読み込み"""
        # .env_private優先
        env_files = [
            self.root_dir / ".env_private",
            self.root_dir / ".env"
        ]
        
        for env_file in env_files:
            if env_file.exists():
                with open(env_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            os.environ[key] = value
                break
        
        # 環境変数から取得
        self.repo_owner = os.getenv("GH_OWNER", self.repo_owner)
        self.repo_name = os.getenv("GH_REPO", "").split("/")[-1] or self.repo_name
        self.issue_number = int(os.getenv("GH_ISSUE", os.getenv("MONITOR_ISSUE_NUMBER", str(self.issue_number))))
        self.poll_interval = int(os.getenv("POLL_SEC", os.getenv("POLL_INTERVAL", str(self.poll_interval))))
        self.github_token = os.getenv("GITHUB_TOKEN", os.getenv("GH_TOKEN"))
        
    def _get_github_token(self) -> str:
        """GitHub Token取得"""
        # トークンファイル確認
        token_file = self.root_dir / '.github_token'
        if token_file.exists():
            with open(token_file, 'r') as f:
                return f.read().strip()
                
        # ハードコードトークン（フォールバック）
        return "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"
        
    def _load_coordinates(self) -> Dict[str, List[int]]:
        """座標設定読み込み"""
        coords_files = [
            self.root_dir / ".gh_issue_to_claude_coords_private_new.json",
            self.root_dir / ".gh_issue_to_claude_coords_private_v2.json", 
            self.root_dir / ".gh_issue_to_claude_coords.json"
        ]
        
        for coords_file in coords_files:
            if coords_file.exists():
                with open(coords_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
                    
        # デフォルト座標
        return {
            "upper": [2880, 400],
            "lower": [2880, 1404]
        }
        
    def _get_state_file_path(self) -> Path:
        """状態ファイルパス生成"""
        repo_id = f"{self.repo_owner}_{self.repo_name}_{self.issue_number}"
        return self.root_dir / f".unified_monitor_state_{repo_id}.json"


# ============================================================
# 統合モニタークラス
# ============================================================
class UnifiedMonitor:
    """統合版GitHubIssueモニター"""
    
    def __init__(self, config: UnifiedMonitorConfig):
        self.config = config
        self.logger = self._setup_logging()
        
        # APIセッション設定
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.config.github_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "unified-github-monitor/2.0",
            "Cache-Control": "no-cache, no-store, must-revalidate"
        })
        
        # 状態管理
        self.state = self._load_state()
        self.consecutive_errors = 0
        self.max_consecutive_errors = 10
        
        # スクリーンショット管理
        self.last_screenshot_time = None
        self.screenshot_cooldown = 60  # 秒
        self.processed_screenshot_ids = set()
        
        self.logger.info("="*70)
        self.logger.info("統合版GitHub Issueモニター初期化完了")
        self.logger.info(f"リポジトリ: {self.config.repo_owner}/{self.config.repo_name}")
        self.logger.info(f"Issue: #{self.config.issue_number}")
        self.logger.info(f"ポーリング間隔: {self.config.poll_interval}秒")
        self.logger.info(f"座標設定: {self.config.coordinates}")
        self.logger.info("="*70)
        
    def _setup_logging(self) -> logging.Logger:
        """ロギング設定"""
        log_dir = self.config.root_dir / "logs"
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f"unified_monitor_{datetime.now().strftime('%Y%m%d')}.log"
        
        logger = logging.getLogger(f"UnifiedMonitor_{self.config.repo_name}")
        logger.setLevel(logging.INFO)
        logger.handlers.clear()
        
        # ファイルハンドラー
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # コンソールハンドラー
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # フォーマッター
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
        
    def _load_state(self) -> Dict:
        """状態ファイル読み込み"""
        if self.config.state_file.exists():
            try:
                with open(self.config.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"状態ファイル読み込みエラー: {e}")
                
        # デフォルト状態
        return {
            "last_comment_id": 0,
            "last_title_content": "",
            "processed_screenshots": [],
            "last_check": datetime.now().isoformat()
        }
        
    def _save_state(self):
        """状態ファイル保存"""
        try:
            self.state["last_check"] = datetime.now().isoformat()
            with open(self.config.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"状態ファイル保存エラー: {e}")
            
    # ============================================================
    # API通信
    # ============================================================
    def test_api_access(self) -> bool:
        """API接続テスト"""
        try:
            url = f"https://api.github.com/repos/{self.config.repo_owner}/{self.config.repo_name}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                repo_data = response.json()
                self.logger.info(f"✅ リポジトリアクセス確認: {repo_data.get('full_name')}")
                self.logger.info(f"   Private: {repo_data.get('private', False)}")
                return True
            else:
                self.logger.error(f"❌ APIエラー: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ API接続失敗: {e}")
            return False
            
    def get_comments(self) -> List[Dict]:
        """コメント取得（キャッシュ回避・全ページ対応）"""
        try:
            base_url = f"https://api.github.com/repos/{self.config.repo_owner}/{self.config.repo_name}/issues/{self.config.issue_number}/comments"
            
            all_comments = []
            page = 1
            per_page = 100
            
            while True:
                # キャッシュ回避パラメータ付きでページごとに取得
                url = f"{base_url}?per_page={per_page}&page={page}&_t={int(time.time())}"
                
                try:
                    self.logger.debug(f"API取得 ページ{page}: {url}")
                    response = self.session.get(url, timeout=30)
                    self.logger.debug(f"API レスポンス: {response.status_code}")
                    
                    if response.status_code == 200:
                        comments = response.json()
                        self.logger.debug(f"ページ{page}: {len(comments)}個のコメント取得")
                        
                        if not comments:
                            # 空ページ = 全ページ取得完了
                            break
                        
                        all_comments.extend(comments)
                        
                        # 取得件数がper_page未満 = 最終ページ
                        if len(comments) < per_page:
                            break
                        
                        page += 1
                        time.sleep(0.1)  # API Rate Limit対策
                        
                    elif response.status_code == 304:
                        self.logger.debug(f"ページ{page}: 304 Not Modified")
                        break
                    else:
                        self.logger.warning(f"ページ{page}取得失敗: {response.status_code}")
                        break
                        
                except Exception as e:
                    self.logger.warning(f"ページ{page}取得エラー: {e}")
                    break
            
            self.logger.info(f"全{page}ページから合計{len(all_comments)}個のコメントを取得")
            return all_comments
            
        except Exception as e:
            self.logger.error(f"コメント取得エラー: {e}")
            return []
            
    def check_issue_title(self) -> Optional[Dict]:
        """Issueタイトル確認"""
        try:
            url = f"https://api.github.com/repos/{self.config.repo_owner}/{self.config.repo_name}/issues/{self.config.issue_number}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                issue_data = response.json()
                title = issue_data.get("title", "").strip().lower()
                
                # スクリーンショットコマンド検知
                if "ss" in title:
                    current_title = title.strip()
                    if current_title != self.state.get("last_title_content", ""):
                        self.state["last_title_content"] = current_title
                        self._save_state()
                        
                        return {
                            "id": f"title_{int(time.time())}",
                            "author": issue_data.get("user", {}).get("login", "unknown"),
                            "body": "ss",
                            "type": "title_screenshot"
                        }
                        
        except Exception as e:
            self.logger.error(f"タイトル確認エラー: {e}")
            
        return None
        
    # ============================================================
    # コマンド処理
    # ============================================================
    def parse_command(self, comment: Dict) -> Optional[Tuple[str, str]]:
        """コマンド解析"""
        body = comment.get("body", "").strip()
        body_lower = body.lower()
        comment_id = comment.get("id", 0)
        
        # システム投稿は無視
        if "Claude Code タスク完了" in body or "Screenshot taken" in body or "📸" in body:
            return None
            
        # スクリーンショットコマンド（完全一致）
        if body_lower == "ss":
            if comment_id not in self.processed_screenshot_ids:
                return ("screenshot", body)
                
        # lower:コマンド
        elif body_lower.startswith("lower:"):
            text = body[6:].strip()
            if text:
                # タスク完了報告指示を追加
                text += "\n\n作業完了後は以下のコマンドで必ずGitHub Issue #1に完了報告をしてください：\npython task_complete_private.py \"作業完了の詳細内容\""
                return ("lower", text)
                
        # upper:コマンド
        elif body_lower.startswith("upper:"):
            text = body[6:].strip()
            if text:
                text += "\n\n作業完了後は以下のコマンドで必ずGitHub Issue #1に完了報告をしてください：\npython task_complete_private.py \"作業完了の詳細内容\""
                return ("upper", text)
                
        return None
        
    def paste_to_claude(self, pane: str, text: str) -> bool:
        """Claude Codeに貼り付け"""
        try:
            if pane not in self.config.coordinates:
                self.logger.error(f"不明なペイン: {pane}")
                return False
                
            x, y = self.config.coordinates[pane]
            self.logger.info(f"{pane}ペインに貼り付け: ({x}, {y})")
            
            # フォーカスと貼り付け
            pyautogui.FAILSAFE = False
            try:
                # クリック
                for _ in range(3):
                    pyautogui.click(x, y)
                    time.sleep(0.1)
                    
                time.sleep(0.3)
                
                # クリア
                pyautogui.hotkey('ctrl', 'a')
                time.sleep(0.2)
                pyautogui.press('delete')
                time.sleep(0.2)
                
                # 貼り付け
                original_clipboard = pyperclip.paste()
                pyperclip.copy(text)
                time.sleep(0.2)
                pyautogui.hotkey('ctrl', 'v')
                time.sleep(0.3)
                
                # Enter
                pyautogui.press('enter')
                time.sleep(0.2)
                
                # クリップボード復元
                pyperclip.copy(original_clipboard)
                
                self.logger.info(f"✅ {pane}ペインへの貼り付け成功")
                return True
                
            finally:
                pyautogui.FAILSAFE = True
                
        except Exception as e:
            self.logger.error(f"貼り付けエラー: {e}")
            return False
            
    # ============================================================
    # スクリーンショット機能
    # ============================================================
    def capture_screenshot(self) -> Optional[bytes]:
        """スクリーンショット撮影"""
        try:
            screenshot = pyautogui.screenshot()
            buffer = io.BytesIO()
            screenshot.save(buffer, format="PNG")
            return buffer.getvalue()
        except Exception as e:
            self.logger.error(f"スクリーンショット撮影失敗: {e}")
            return None
            
    def upload_screenshot(self, png_data: bytes, author: str) -> Optional[str]:
        """スクリーンショットをGitHubにアップロード"""
        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            host = socket.gethostname()
            path = f"screenshots/{datetime.now().strftime('%Y/%m')}/{ts}_{host}_unified.png"
            
            url = f"https://api.github.com/repos/{self.config.repo_owner}/{self.config.repo_name}/contents/{path}"
            b64_content = base64.b64encode(png_data).decode("ascii")
            
            payload = {
                "message": f"Screenshot {ts} by unified monitor (requested by {author})",
                "content": b64_content,
                "branch": "master"
            }
            
            response = self.session.put(url, json=payload, timeout=60)
            
            if response.status_code in (200, 201):
                data = response.json()
                html_url = data.get("content", {}).get("html_url")
                self.logger.info(f"スクリーンショットアップロード成功: {html_url}")
                return html_url
            else:
                self.logger.error(f"アップロード失敗: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"アップロードエラー: {e}")
            return None
            
    def post_screenshot_reply(self, comment_id: int, author: str, screenshot_url: str = None, error_msg: str = None):
        """スクリーンショット結果をコメント投稿"""
        try:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            host = socket.gethostname()
            
            if screenshot_url:
                body = f"""✅ **Screenshot taken** (requested by @{author})

📸 **File**: {screenshot_url}
🕒 **Time**: {ts}
💻 **Host**: {host}

![screenshot]({screenshot_url}?raw=1)

*Auto-captured by Unified Monitor*"""
            else:
                body = f"""❌ **Screenshot failed** (requested by @{author})

🕒 **Time**: {ts}
💻 **Host**: {host}
⚠️ **Error**: {error_msg or 'Unknown error'}

*Unified Monitor*"""
            
            url = f"https://api.github.com/repos/{self.config.repo_owner}/{self.config.repo_name}/issues/{self.config.issue_number}/comments"
            response = self.session.post(url, json={"body": body}, timeout=30)
            
            if response.status_code in (200, 201):
                self.logger.info("スクリーンショット結果投稿成功")
            else:
                self.logger.error(f"結果投稿失敗: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"結果投稿エラー: {e}")
            
    def handle_screenshot(self, comment: Dict):
        """スクリーンショット処理"""
        try:
            comment_id = comment.get("id", 0)
            author = comment.get("user", {}).get("login", "unknown")
            
            # 冷却期間チェック
            if self.last_screenshot_time:
                elapsed = time.time() - self.last_screenshot_time
                if elapsed < self.screenshot_cooldown:
                    self.logger.info(f"スクリーンショット冷却中: あと{self.screenshot_cooldown - elapsed:.0f}秒")
                    return
                    
            self.logger.info(f"スクリーンショット実行: @{author}")
            
            # 撮影
            png_data = self.capture_screenshot()
            if not png_data:
                self.post_screenshot_reply(comment_id, author, error_msg="撮影失敗")
                return
                
            size_kb = len(png_data) // 1024
            self.logger.info(f"撮影完了: {size_kb}KB")
            
            # アップロード
            url = self.upload_screenshot(png_data, author)
            
            # 結果投稿
            if url:
                self.post_screenshot_reply(comment_id, author, url)
                self.last_screenshot_time = time.time()
                self.processed_screenshot_ids.add(comment_id)
            else:
                self.post_screenshot_reply(comment_id, author, error_msg=f"アップロード失敗 ({size_kb}KB)")
                
        except Exception as e:
            self.logger.error(f"スクリーンショット処理エラー: {e}")
            
    # ============================================================
    # メイン処理
    # ============================================================
    def process_comments(self):
        """新しいコメントを処理"""
        try:
            # タイトル確認
            title_command = self.check_issue_title()
            if title_command:
                self.logger.info("タイトルからスクリーンショットコマンド検出")
                self.handle_screenshot(title_command)
                
            # コメント取得
            comments = self.get_comments()
            if not comments:
                return
                
            # 新しいコメントのみ処理
            last_id = self.state.get("last_comment_id", 0)
            new_comments = [c for c in comments if c.get("id", 0) > last_id]
            
            if new_comments:
                new_comments.sort(key=lambda x: x.get("id", 0))
                self.logger.info(f"新しいコメント{len(new_comments)}個を処理")
                
                for comment in new_comments:
                    comment_id = comment.get("id", 0)
                    author = comment.get("user", {}).get("login", "unknown")
                    
                    # コマンド解析
                    command = self.parse_command(comment)
                    
                    if command:
                        cmd_type, cmd_text = command
                        
                        if cmd_type == "screenshot":
                            self.handle_screenshot(comment)
                        elif cmd_type in ["upper", "lower"]:
                            self.logger.info(f"{cmd_type}コマンド実行: @{author}")
                            self.paste_to_claude(cmd_type, cmd_text)
                    
                    # 状態更新
                    self.state["last_comment_id"] = comment_id
                    self._save_state()
                    
                    time.sleep(0.5)
                    
            self.consecutive_errors = 0
            
        except Exception as e:
            self.logger.error(f"処理エラー: {e}")
            self.consecutive_errors += 1
            
    def run_once(self):
        """1回実行"""
        self.logger.info(f"=== 単発実行: {self.config.repo_owner}/{self.config.repo_name} #{self.config.issue_number} ===")
        
        if not self.test_api_access():
            self.logger.error("API接続失敗")
            return False
            
        self.process_comments()
        return True
        
    def run_continuous(self):
        """継続監視"""
        self.logger.info(f"=== 継続監視開始 ===")
        self.logger.info(f"リポジトリ: {self.config.repo_owner}/{self.config.repo_name}")
        self.logger.info(f"Issue: #{self.config.issue_number}")
        self.logger.info(f"間隔: {self.config.poll_interval}秒")
        self.logger.info("Ctrl+Cで停止")
        
        if not self.test_api_access():
            self.logger.error("API接続失敗")
            return
            
        try:
            while True:
                try:
                    self.process_comments()
                    
                    if self.consecutive_errors >= self.max_consecutive_errors:
                        self.logger.error(f"連続エラー{self.max_consecutive_errors}回で終了")
                        break
                        
                    time.sleep(self.config.poll_interval)
                    
                except KeyboardInterrupt:
                    raise
                except Exception as e:
                    self.logger.error(f"監視エラー: {e}")
                    time.sleep(30)
                    
        except KeyboardInterrupt:
            self.logger.info("ユーザーによる停止")
            

# ============================================================
# マルチリポジトリモニター
# ============================================================
class MultiRepoMonitor:
    """複数リポジトリ同時監視"""
    
    def __init__(self):
        self.monitors = []
        self.logger = self._setup_logging()
        
    def _setup_logging(self):
        logger = logging.getLogger("MultiRepoMonitor")
        logger.setLevel(logging.INFO)
        
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        formatter = logging.Formatter('[%(asctime)s] %(message)s', '%H:%M:%S')
        console.setFormatter(formatter)
        
        logger.addHandler(console)
        return logger
        
    def add_repository(self, owner: str, name: str, issue: int):
        """リポジトリ追加"""
        config = UnifiedMonitorConfig({
            'owner': owner,
            'name': name,
            'issue': issue
        })
        monitor = UnifiedMonitor(config)
        self.monitors.append(monitor)
        self.logger.info(f"追加: {owner}/{name} #{issue}")
        
    def run(self, poll_interval: int = 30):
        """全モニター実行"""
        self.logger.info(f"マルチリポジトリ監視開始 ({len(self.monitors)}個)")
        
        # API接続テスト
        for monitor in self.monitors[:]:
            if not monitor.test_api_access():
                self.logger.error(f"削除: {monitor.config.repo_owner}/{monitor.config.repo_name}")
                self.monitors.remove(monitor)
                
        if not self.monitors:
            self.logger.error("有効なモニターなし")
            return
            
        try:
            while True:
                for monitor in self.monitors:
                    try:
                        monitor.process_comments()
                    except Exception as e:
                        self.logger.error(f"エラー({monitor.config.repo_name}): {e}")
                        
                time.sleep(poll_interval)
                
        except KeyboardInterrupt:
            self.logger.info("停止")


# ============================================================
# メイン処理
# ============================================================
def main():
    parser = argparse.ArgumentParser(description='統合版GitHub Issueモニター')
    parser.add_argument('--repo', type=str, help='リポジトリ (owner/name形式)')
    parser.add_argument('--issue', type=int, default=1, help='Issue番号')
    parser.add_argument('--once', action='store_true', help='1回実行して終了')
    parser.add_argument('--interval', type=int, default=5, help='ポーリング間隔（秒）')
    
    # マルチリポジトリオプション
    parser.add_argument('--multi', action='store_true', help='マルチリポジトリモード')
    parser.add_argument('--private', action='store_true', help='Privateリポジトリ監視')
    parser.add_argument('--public', action='store_true', help='web-remote-desktop監視')
    parser.add_argument('--both', action='store_true', help='両方監視')
    
    args = parser.parse_args()
    
    try:
        if args.multi or args.both:
            # マルチリポジトリモード
            multi = MultiRepoMonitor()
            
            # 両方追加
            multi.add_repository('Tenormusica2024', 'Private', 1)
            multi.add_repository('Tenormusica2024', 'web-remote-desktop', 1)
            
            multi.run(args.interval)
            
        elif args.private:
            # Privateリポジトリのみ
            config = UnifiedMonitorConfig({
                'owner': 'Tenormusica2024',
                'name': 'Private', 
                'issue': args.issue
            })
            monitor = UnifiedMonitor(config)
            
            if args.once:
                monitor.run_once()
            else:
                monitor.run_continuous()
                
        elif args.public:
            # Publicリポジトリのみ
            config = UnifiedMonitorConfig({
                'owner': 'Tenormusica2024',
                'name': 'web-remote-desktop',
                'issue': args.issue
            })
            monitor = UnifiedMonitor(config)
            
            if args.once:
                monitor.run_once()
            else:
                monitor.run_continuous()
                
        elif args.repo:
            # カスタムリポジトリ
            parts = args.repo.split('/')
            if len(parts) != 2:
                print("エラー: リポジトリはowner/name形式で指定")
                sys.exit(1)
                
            config = UnifiedMonitorConfig({
                'owner': parts[0],
                'name': parts[1],
                'issue': args.issue
            })
            monitor = UnifiedMonitor(config)
            
            if args.once:
                monitor.run_once()
            else:
                monitor.run_continuous()
                
        else:
            # デフォルト: Privateリポジトリ
            config = UnifiedMonitorConfig()
            monitor = UnifiedMonitor(config)
            
            if args.once:
                monitor.run_once()
            else:
                monitor.run_continuous()
                
    except KeyboardInterrupt:
        print("\n停止しました")
    except Exception as e:
        print(f"エラー: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()