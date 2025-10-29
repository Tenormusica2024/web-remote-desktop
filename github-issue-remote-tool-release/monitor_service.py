#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Issue → Claude Code 常駐監視サービス（汎用版）
config.jsonから設定を読み込んで任意のGitHub Issueを監視
"""

import os, sys, time, json, logging
from pathlib import Path
import datetime
import requests
import pyautogui
import pyperclip
import traceback
import io, base64, socket

# ログ設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('monitor_service.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class IssueMonitor:
    def __init__(self):
        self.load_config()
        self.setup_files()
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.gh_token}",
            "Accept": "application/vnd.github+json", 
            "User-Agent": "github-issue-remote-tool/1.0",
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache"
        })
        self.consecutive_errors = 0
        self.max_consecutive_errors = 10
        
        self.last_screenshot_time = None
        self.screenshot_cooldown_seconds = 60
        self.processed_screenshot_comments = set()
        
        logger.info(f"Issue監視サービス初期化完了")
        logger.info(f"Repository: {self.gh_repo} Issue #{self.gh_issue}")
        logger.info(f"Poll interval: {self.poll_sec}秒")
    
    def load_config(self):
        """config.jsonから設定読み込み"""
        config_file = Path("config.json")
        if not config_file.exists():
            raise RuntimeError("config.jsonが見つかりません。setup_wizard.pyを実行してください")
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            self.gh_token = config.get("github_token")
            self.gh_repo = config.get("github_repo")
            self.gh_issue = str(config.get("issue_number"))
            self.poll_sec = int(config.get("poll_interval", 5))
            self.coords = config.get("claude_code_coords", {})
            
            if not all([self.gh_token, self.gh_repo, self.gh_issue]):
                raise RuntimeError("config.jsonに必須項目が不足しています")
                
            self.owner, self.repo = self.gh_repo.split("/", 1)
            self.issue_num = int(self.gh_issue)
            
            self.upper_coords = self.coords.get("upper")
            self.lower_coords = self.coords.get("lower")
            
            if not self.upper_coords or not self.lower_coords:
                raise RuntimeError("Claude Code座標が設定されていません")
                
            logger.info(f"設定読み込み完了: {config_file}")
            
        except json.JSONDecodeError as e:
            raise RuntimeError(f"config.json解析エラー: {e}")
        except Exception as e:
            raise RuntimeError(f"設定読み込みエラー: {e}")
    
    def setup_files(self):
        """状態ファイル設定"""
        self.state_file = Path(f".monitor_state_{self.gh_repo.replace('/', '_')}_{self.gh_issue}.json")
        logger.info(f"状態ファイル: {self.state_file}")
    
    def capture_screenshot(self):
        """スクリーンショット撮影"""
        try:
            shot = pyautogui.screenshot()
            buf = io.BytesIO()
            shot.save(buf, format="PNG")
            return buf.getvalue()
        except Exception as e:
            logger.error(f"スクリーンショット撮影エラー: {e}")
            return None
    
    def upload_screenshot_to_github(self, png_data, filename):
        """GitHubにスクリーンショットアップロード"""
        try:
            path_in_repo = f"screenshots/{datetime.datetime.now().strftime('%Y/%m')}/{filename}"
            b64 = base64.b64encode(png_data).decode("ascii")
            
            url = f"https://api.github.com/repos/{self.owner}/{self.repo}/contents/{path_in_repo}"
            payload = {
                "message": f"Screenshot: {filename}",
                "content": b64,
                "branch": "master",
            }
            
            r = self.session.put(url, json=payload, timeout=60)
            if r.status_code not in (200, 201):
                logger.error(f"スクリーンショットアップロード失敗: {r.status_code} {r.text}")
                return None
                
            data = r.json()
            html_url = data.get("content", {}).get("html_url")
            logger.info(f"スクリーンショットアップロード成功: {html_url}")
            return html_url
            
        except Exception as e:
            logger.error(f"スクリーンショットアップロードエラー: {e}")
            return None
    
    def post_screenshot_to_issue(self, image_url, filename, trigger_comment=""):
        """Issueにスクリーンショットコメント投稿"""
        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            host = socket.gethostname()
            
            raw_url = image_url + "?raw=1" if image_url else ""
            body = f"""📸 **Screenshot**
- Time: `{timestamp}`
- Host: `{host}`
- Trigger: {trigger_comment[:100] if trigger_comment else "Remote command"}

![screenshot]({raw_url})
"""
            
            url = f"https://api.github.com/repos/{self.owner}/{self.repo}/issues/{self.issue_num}/comments"
            r = self.session.post(url, json={"body": body}, timeout=30)
            
            if r.status_code in (200, 201):
                logger.info(f"スクリーンショットコメント投稿成功: {filename}")
                return True
            else:
                logger.error(f"スクリーンショットコメント投稿失敗: {r.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"スクリーンショットコメント投稿エラー: {e}")
            return False
    
    def take_and_post_screenshot(self, trigger_comment=""):
        """スクリーンショット撮影・投稿"""
        try:
            logger.info("スクリーンショット撮影開始...")
            
            png_data = self.capture_screenshot()
            if not png_data:
                return False
                
            size_kb = len(png_data) // 1024
            logger.info(f"スクリーンショット撮影完了: {size_kb}KB")
            
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            host = socket.gethostname()
            filename = f"{ts}_{host}.png"
            
            image_url = self.upload_screenshot_to_github(png_data, filename)
            if not image_url:
                return False
            
            success = self.post_screenshot_to_issue(image_url, filename, trigger_comment)
            
            if success:
                logger.info(f"スクリーンショット投稿完了: {filename}")
            
            return success
            
        except Exception as e:
            logger.error(f"スクリーンショット投稿エラー: {e}")
            return False
    
    def load_state(self):
        """状態ファイル読み込み"""
        if self.state_file.exists():
            try:
                content = self.state_file.read_text(encoding='utf-8')
                return json.loads(content)
            except Exception as e:
                logger.warning(f"状態ファイル読み込みエラー: {e}")
        return {"last_comment_id": 0, "comments_etag": None}
    
    def save_state(self, state):
        """状態ファイル保存"""
        try:
            self.state_file.write_text(json.dumps(state, indent=2), encoding='utf-8')
        except Exception as e:
            logger.error(f"状態ファイル保存エラー: {e}")
    
    def get_comments_with_cache_bypass(self):
        """GitHub APIからコメント取得（キャッシュ回避）"""
        base_url = f"https://api.github.com/repos/{self.owner}/{self.repo}/issues/{self.issue_num}/comments"
        
        all_comments = []
        page = 1
        per_page = 100
        
        while True:
            url = f"{base_url}?per_page={per_page}&page={page}&_t={int(time.time())}"
            
            try:
                r = self.session.get(url, timeout=30)
                
                if r.status_code == 200:
                    comments = r.json()
                    
                    if not comments:
                        break
                    
                    all_comments.extend(comments)
                    
                    if len(comments) < per_page:
                        break
                    
                    page += 1
                    time.sleep(0.1)
                    
                elif r.status_code == 304:
                    break
                else:
                    logger.warning(f"ページ{page}取得失敗: {r.status_code}")
                    break
                    
            except Exception as e:
                logger.warning(f"ページ{page}取得エラー: {e}")
                break
        
        logger.info(f"全{page}ページから合計{len(all_comments)}個のコメントを取得")
        return all_comments, None
    
    def paste_to_claude_code(self, text, auto_enter=True, pane="lower"):
        """Claude Codeに貼り付け"""
        try:
            if pane == "upper":
                x, y = self.upper_coords
            else:
                x, y = self.lower_coords
            
            pyautogui.moveTo(x, y, duration=0.1)
            pyautogui.click()
            time.sleep(0.1)
            
            old_clip = None
            try:
                old_clip = pyperclip.paste()
            except Exception:
                pass
            
            pyperclip.copy(text)
            time.sleep(0.1)
            pyautogui.hotkey("ctrl", "v")
            time.sleep(0.2)
            
            if auto_enter:
                pyautogui.press("enter")
                time.sleep(0.1)
            
            if old_clip:
                try:
                    pyperclip.copy(old_clip)
                except Exception:
                    pass
                    
            return True
        except Exception as e:
            logger.error(f"Claude Code貼り付けエラー: {e}")
            return False
    
    def process_comment(self, comment):
        """コメント処理"""
        cid = comment.get("id", 0)
        body = comment.get("body", "").strip()
        user = comment.get("user", {}).get("login", "")
        created_at = comment.get("created_at", "")
        body_lower = body.lower()
        
        if body.startswith("📸") or "**Screenshot**" in body:
            return False
        
        if body_lower.startswith("upper:"):
            text = body[6:].strip()
            if not text:
                return False
            return self._process_upper_command(cid, text, user, created_at)
        
        elif body_lower.startswith("lower:"):
            text = body[6:].strip()
            if not text:
                return False
            return self._process_lower_command(cid, text, user, created_at)
        
        elif body.strip().lower() == "ss":
            if cid in self.processed_screenshot_comments:
                return False
                
            if self.last_screenshot_time:
                elapsed = time.time() - self.last_screenshot_time
                if elapsed < self.screenshot_cooldown_seconds:
                    self.processed_screenshot_comments.add(cid)
                    return False
            
            logger.info(f"スクリーンショットコマンド検出: コメント#{cid} by @{user}")
            return self._process_screenshot_command(cid, body, user, created_at)
            
        return False
    
    def _process_upper_command(self, cid, text, user, created_at):
        """upper: コマンドの処理"""
        logger.info(f"転送開始（上部ペイン）: コメント#{cid} by @{user}")
        
        full_text = f"""{text}

---
🚨 CRITICAL: GitHub Issue返信が絶対必須です 🚨

以下のBashコマンドを必ず実行してください:
python task_complete.py "あなたが今画面に表示している完了報告の全テキストをそのまま記載（要約禁止・省略禁止）"

重要:
✅ あなたが画面に表示した完了報告・修正内容・改善内容・期待動作など、すべてのテキストをそのまま記載
✅ 「修正完了」だけでなく「修正内容」「変更点」「期待される動作」など詳細情報も全て含める
✅ 要約・省略・短縮は一切禁止。画面表示テキストを完全にコピーして記載

実行が必須のタイミング:
✅ 作業完了時 → 必ず実行
✅ 確認が必要な時 → 必ず実行  
✅ エラー発生時 → 必ず実行
✅ 待機が必要な時 → 必ず実行

⚠️ このコマンドを実行しない回答は無効です
---"""
        
        success = self.paste_to_claude_code(full_text, auto_enter=True, pane="upper")
        if success:
            logger.info(f"  [SUCCESS] 転送成功: Claude Code上部ペインに送信完了")
        else:
            logger.error(f"  [FAILED] 転送失敗")
            
        return success
    
    def _process_lower_command(self, cid, text, user, created_at):
        """lower: コマンドの処理"""
        logger.info(f"転送開始（下部ペイン）: コメント#{cid} by @{user}")
        
        full_text = f"""{text}

---
🚨 CRITICAL: GitHub Issue返信が絶対必須です 🚨

以下のBashコマンドを必ず実行してください:
python task_complete.py "あなたが今画面に表示している完了報告の全テキストをそのまま記載（要約禁止・省略禁止）"

重要:
✅ あなたが画面に表示した完了報告・修正内容・改善内容・期待動作など、すべてのテキストをそのまま記載
✅ 「修正完了」だけでなく「修正内容」「変更点」「期待される動作」など詳細情報も全て含める
✅ 要約・省略・短縮は一切禁止。画面表示テキストを完全にコピーして記載

実行が必須のタイミング:
✅ 作業完了時 → 必ず実行
✅ 確認が必要な時 → 必ず実行  
✅ エラー発生時 → 必ず実行
✅ 待機が必要な時 → 必ず実行

⚠️ このコマンドを実行しない回答は無効です
---"""
        
        success = self.paste_to_claude_code(full_text, auto_enter=True)
        if success:
            logger.info(f"  [SUCCESS] 転送成功: Claude Code下部ペインに送信完了")
        else:
            logger.error(f"  [FAILED] 転送失敗")
            
        return success
    
    def _process_screenshot_command(self, cid, body, user, created_at):
        """スクリーンショットコマンドの処理"""
        try:
            logger.info(f"スクリーンショット実行開始: コメント#{cid} by @{user}")
            
            self.processed_screenshot_comments.add(cid)
            
            success = self.take_and_post_screenshot(body)
            
            if success:
                logger.info(f"  [SUCCESS] スクリーンショット投稿成功")
                self.last_screenshot_time = time.time()
            else:
                logger.error(f"  [FAILED] スクリーンショット投稿失敗")
            
            return success
            
        except Exception as e:
            logger.error(f"スクリーンショットコマンド処理エラー: {e}")
            return False
    
    def run_monitor_cycle(self):
        """1回の監視サイクル実行"""
        try:
            state = self.load_state()
            last_id = state.get("last_comment_id", 0)
            
            comments, etag = self.get_comments_with_cache_bypass()
            
            if not comments:
                return True
            
            def is_processable_comment(comment):
                body = comment.get("body", "").strip()
                body_lower = body.lower()
                comment_id = comment.get("id", 0)
                
                if body.startswith("📸") or "**Screenshot**" in body:
                    return False
                
                if body_lower.startswith("upper:"):
                    return True
                
                if body_lower.startswith("lower:"):
                    return True
                
                if body.strip().lower() == "ss":
                    if comment_id in self.processed_screenshot_comments:
                        return False
                    return True
                    
                return False
            
            processable_comments = [c for c in comments if is_processable_comment(c)]
            new_comments = [c for c in processable_comments if c.get("id", 0) > last_id]
            
            if new_comments:
                new_comments.sort(key=lambda x: x.get("id", 0))
                logger.info(f"未処理コマンドコメント {len(new_comments)}個を処理開始")
                
                for comment in new_comments:
                    success = self.process_comment(comment)
                    if success:
                        state["last_comment_id"] = comment.get("id", 0)
                        self.save_state(state)
                    time.sleep(0.5)
                
                logger.info(f"処理完了: {len(new_comments)}個のコメントを転送")
            
            self.consecutive_errors = 0
            return True
            
        except Exception as e:
            logger.error(f"監視サイクルエラー: {type(e).__name__}: {e}")
            self.consecutive_errors += 1
            return False
    
    def run(self):
        """メイン監視ループ"""
        logger.info("Issue監視サービス開始")
        logger.info("Ctrl+Cで停止")
        
        while True:
            try:
                success = self.run_monitor_cycle()
                
                if not success:
                    if self.consecutive_errors >= self.max_consecutive_errors:
                        logger.error(f"連続エラー{self.max_consecutive_errors}回に達したため終了")
                        break
                    
                    error_wait = min(60, self.poll_sec * (1 + self.consecutive_errors))
                    logger.warning(f"エラー後の待機: {error_wait}秒")
                    time.sleep(error_wait)
                else:
                    time.sleep(self.poll_sec)
                    
            except KeyboardInterrupt:
                logger.info("ユーザーによる停止要求")
                break
            except Exception as e:
                logger.error(f"予期しないエラー: {e}")
                time.sleep(30)
        
        logger.info("Issue監視サービス終了")

def main():
    try:
        monitor = IssueMonitor()
        monitor.run()
    except Exception as e:
        logger.error(f"初期化エラー: {e}")
        logger.debug(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()