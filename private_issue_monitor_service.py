#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Private Issue → Claude Code 常駐監視サービス (改良版)
- 確実な常駐実行
- 強化されたエラーハンドリング
- GitHub APIキャッシュ対応
- 自動復旧機能
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
    level=logging.DEBUG,  # 詳細ログ有効化
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('private_issue_monitor.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class PrivateIssueMonitor:
    def __init__(self):
        self.load_config()
        self.setup_files()
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.gh_token}",
            "Accept": "application/vnd.github+json", 
            "User-Agent": "private-issue-monitor-service/2.0",
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache"
        })
        self.consecutive_errors = 0
        self.max_consecutive_errors = 10
        
        # スクリーンショット投稿履歴管理
        self.last_screenshot_time = None
        self.screenshot_cooldown_seconds = 60  # 60秒間の冷却期間
        self.processed_screenshot_comments = set()  # 処理済みのssコメントID
        
        logger.info(f"Private Issue監視サービス初期化完了")
        logger.info(f"Repository: {self.gh_repo} Issue #{self.gh_issue}")
        logger.info(f"Poll interval: {self.poll_sec}秒")
    
    def load_config(self):
        """設定読み込み"""
        # .env_private優先で環境変数読み込み
        env_file = Path(".env_private")
        if env_file.exists():
            logger.info(f"設定ファイル読み込み: {env_file}")
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key] = value
        
        self.gh_repo = os.getenv("GH_REPO")
        self.gh_issue = os.getenv("GH_ISSUE") 
        self.gh_token = os.getenv("GH_TOKEN")
        self.poll_sec = int(os.getenv("POLL_SEC", "5"))
        
        if not all([self.gh_repo, self.gh_issue, self.gh_token]):
            raise RuntimeError("必須環境変数が不足: GH_REPO, GH_ISSUE, GH_TOKEN")
            
        self.owner, self.repo = self.gh_repo.split("/", 1)
        self.issue_num = int(self.gh_issue)
    
    def setup_files(self):
        """ファイル設定"""
        self.state_file = Path(".gh_issue_to_claude_state_private_service.json")
        self.coords_file = Path(".gh_issue_to_claude_coords_private_new.json")
        
        if not self.coords_file.exists():
            raise RuntimeError(f"座標ファイルが見つかりません: {self.coords_file}")
        
        # 座標読み込み
        self.coords = json.loads(self.coords_file.read_text(encoding='utf-8'))
        self.upper_coords = self.coords.get("upper")
        self.lower_coords = self.coords.get("lower")
        
        if not self.upper_coords:
            raise RuntimeError("upper座標が設定されていません")
        if not self.lower_coords:
            raise RuntimeError("lower座標が設定されていません")
            
        logger.info(f"Claude Code上ペイン座標: {self.upper_coords}")
        logger.info(f"Claude Code下ペイン座標: {self.lower_coords}")
    
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
            path_in_repo = f"private_screenshots/{datetime.datetime.now().strftime('%Y/%m')}/{filename}"
            b64 = base64.b64encode(png_data).decode("ascii")
            
            url = f"https://api.github.com/repos/{self.owner}/{self.repo}/contents/{path_in_repo}"
            payload = {
                "message": f"Private screenshot: {filename}",
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
        """Issue にスクリーンショットコメント投稿"""
        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            host = socket.gethostname()
            
            raw_url = image_url + "?raw=1" if image_url else ""
            body = f"""📸 **Private Screenshot**
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
            
            # スクリーンショット撮影
            png_data = self.capture_screenshot()
            if not png_data:
                return False
                
            size_kb = len(png_data) // 1024
            logger.info(f"スクリーンショット撮影完了: {size_kb}KB")
            
            # ファイル名生成
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            host = socket.gethostname()
            filename = f"{ts}_{host}_private.png"
            
            # GitHubにアップロード
            image_url = self.upload_screenshot_to_github(png_data, filename)
            if not image_url:
                return False
            
            # Issue にコメント投稿
            success = self.post_screenshot_to_issue(image_url, filename, trigger_comment)
            
            if success:
                logger.info(f"スクリーンショット投稿完了: {filename}")
            
            return success
            
        except Exception as e:
            logger.error(f"スクリーンショット投稿エラー: {e}")
            return False
    
    def load_state(self):
        """状態ファイル読み込み"""
        logger.debug(f"状態ファイル読み込み開始: {self.state_file}")
        if self.state_file.exists():
            try:
                content = self.state_file.read_text(encoding='utf-8')
                logger.debug(f"状態ファイル内容: {content}")
                state = json.loads(content)
                logger.debug(f"読み込み成功: {state}")
                return state
            except Exception as e:
                logger.warning(f"状態ファイル読み込みエラー: {e}")
        else:
            logger.debug("状態ファイルが存在しません")
        default_state = {"last_comment_id": 0, "comments_etag": None}
        logger.debug(f"デフォルト状態を返します: {default_state}")
        return default_state
    
    def save_state(self, state):
        """状態ファイル保存"""
        try:
            self.state_file.write_text(json.dumps(state, indent=2), encoding='utf-8')
        except Exception as e:
            logger.error(f"状態ファイル保存エラー: {e}")
    
    def get_comments_with_cache_bypass(self):
        """GitHub APIからコメント取得（キャッシュ回避・全ページ対応）"""
        base_url = f"https://api.github.com/repos/{self.owner}/{self.repo}/issues/{self.issue_num}/comments"
        
        all_comments = []
        page = 1
        per_page = 100
        
        while True:
            # キャッシュ回避パラメータ付きでページごとに取得
            url = f"{base_url}?per_page={per_page}&page={page}&_t={int(time.time())}"
            
            try:
                logger.debug(f"API取得 ページ{page}: {url}")
                r = self.session.get(url, timeout=30)
                logger.debug(f"API レスポンス: {r.status_code}")
                
                if r.status_code == 200:
                    comments = r.json()
                    logger.debug(f"ページ{page}: {len(comments)}個のコメント取得")
                    
                    if not comments:
                        # 空ページ = 全ページ取得完了
                        break
                    
                    all_comments.extend(comments)
                    
                    # 取得件数がper_page未満 = 最終ページ
                    if len(comments) < per_page:
                        break
                    
                    page += 1
                    time.sleep(0.1)  # API Rate Limit対策
                    
                elif r.status_code == 304:
                    logger.debug(f"ページ{page}: 304 Not Modified")
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
            
            # フォーカス
            # すべてのキーをリリース（誤動作防止）
            try:
                pyautogui.keyUp('win')
                pyautogui.keyUp('alt')
                pyautogui.keyUp('ctrl')
                pyautogui.keyUp('shift')
            except Exception:
                pass
            
            pyautogui.moveTo(x, y, duration=0.1)
            time.sleep(0.1)
            # click()の代わりにmouseDown/mouseUpを使用（ショートカットキー誤発火防止）
            pyautogui.mouseDown()
            time.sleep(0.05)
            pyautogui.mouseUp()
            time.sleep(0.1)
            
            # クリップボード経由で貼り付け
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
            
            # クリップボード復元
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
        
        # システム自身が投稿したスクリーンショットコメントは除外
        if body.startswith("📸") or "**Private Screenshot**" in body:
            logger.debug(f"コメント#{cid}: システム投稿スクリーンショット（スキップ）")
            return False
        
        # upper: コマンドの処理
        if body_lower.startswith("upper:"):
            text = body[6:].strip()  # "upper:"を除去
            if not text:
                logger.info(f"コメント#{cid}: 空のテキスト（スキップ）")
                return False
            return self._process_upper_command(cid, text, user, created_at)
        
        # lower: コマンドの処理
        elif body_lower.startswith("lower:"):
            text = body[6:].strip()  # "lower:"を除去
            if not text:
                logger.info(f"コメント#{cid}: 空のテキスト（スキップ）")
                return False
            return self._process_lower_command(cid, text, user, created_at)
        
        # スクリーンショットコマンドの処理（「ss」のみ、完全一致）
        elif body.strip().lower() == "ss":
            # 既に処理済みのssコメントは無視
            if cid in self.processed_screenshot_comments:
                logger.debug(f"コメント#{cid}: 既に処理済みのssコマンド（スキップ）")
                return False
                
            # 冷却期間チェック
            if self.last_screenshot_time:
                elapsed = time.time() - self.last_screenshot_time
                if elapsed < self.screenshot_cooldown_seconds:
                    remaining = self.screenshot_cooldown_seconds - elapsed
                    logger.info(f"スクリーンショット冷却中: あと{remaining:.0f}秒待機が必要（コメント#{cid}をスキップ）")
                    # このコメントも処理済みとして記録
                    self.processed_screenshot_comments.add(cid)
                    return False
            
            logger.info(f"スクリーンショットコマンド検出: コメント#{cid} by @{user}")
            return self._process_screenshot_command(cid, body, user, created_at)
            
        # その他のコマンドは無視
        return False
    
    def _process_upper_command(self, cid, text, user, created_at):
        """upper: コマンドの処理（上部ペインに送信）"""
        
        safe_user = user.encode('ascii', 'replace').decode('ascii')
        safe_text = text[:100].encode('ascii', 'replace').decode('ascii')
        safe_created = created_at.encode('ascii', 'replace').decode('ascii')
        
        logger.info(f"転送開始（上部ペイン）: コメント#{cid} by @{safe_user}")
        logger.info(f"  作成時刻: {safe_created}")
        logger.info(f"  テキスト: {safe_text}{'...' if len(text) > 100 else ''}")
        
        # GitHub Issue返信指示を追加（すべての回答で必須）
        full_text = f"""{text}

---
🚨🚨🚨 MANDATORY: このメッセージはGitHub Issueから来ています 🚨🚨🚨

【絶対ルール】このメッセージはタスクリスト化して処理してください。

📋 必須実行手順:
1. 必ずTodoWriteツールでタスクリストを作成する
2. 最後のタスクは必ず「GitHub Issueへ報告」にする
3. 各タスクを順次実行する
4. 最終タスクの報告実行まで作業を継続する

以下のBashコマンドを最終タスクで実行:
cd "C:\\Users\\Tenormusica\\Documents\\github-remote-desktop" && python task_complete_private.py "あなたが今画面に表示しているテキストの全文をそのまま記載"

⚠️ 回答の種類に関係なく必ず実行:
- 作業が終わった → 実行
- 質問がある → 実行
- 確認したい → 実行
- エラーが出た → 実行
- 待機する → 実行
- 「了解」だけでも → 実行

❌ このコマンドを実行せずに回答を終えることは禁止
❌ 「後で実行する」は禁止
❌ 回答の長短に関係なく必ず実行
❌ タスクリストなしで作業することは禁止

📝 記載内容: 画面に表示したテキストをそのままコピー（要約・省略禁止）
---"""
        
        success = self.paste_to_claude_code(full_text, auto_enter=True, pane="upper")
        if success:
            logger.info(f"  [SUCCESS] 転送成功: Claude Code上部ペインに送信完了")
        else:
            logger.error(f"  [FAILED] 転送失敗")
            
        return success
    
    def _process_lower_command(self, cid, text, user, created_at):
        """lower: コマンドの処理（下部ペインに送信）"""
        
        safe_user = user.encode('ascii', 'replace').decode('ascii')
        safe_text = text[:100].encode('ascii', 'replace').decode('ascii')
        safe_created = created_at.encode('ascii', 'replace').decode('ascii')
        
        logger.info(f"転送開始（下部ペイン）: コメント#{cid} by @{safe_user}")
        logger.info(f"  作成時刻: {safe_created}")
        logger.info(f"  テキスト: {safe_text}{'...' if len(text) > 100 else ''}")
        
        # GitHub Issue返信指示を追加（すべての回答で必須）
        full_text = f"""{text}

---
🚨🚨🚨 MANDATORY: このメッセージはGitHub Issueから来ています 🚨🚨🚨

【絶対ルール】このメッセージはタスクリスト化して処理してください。

📋 必須実行手順:
1. 必ずTodoWriteツールでタスクリストを作成する
2. 最後のタスクは必ず「GitHub Issueへ報告」にする
3. 各タスクを順次実行する
4. 最終タスクの報告実行まで作業を継続する

以下のBashコマンドを最終タスクで実行:
cd "C:\\Users\\Tenormusica\\Documents\\github-remote-desktop" && python task_complete_private.py "あなたが今画面に表示しているテキストの全文をそのまま記載"

⚠️ 回答の種類に関係なく必ず実行:
- 作業が終わった → 実行
- 質問がある → 実行
- 確認したい → 実行
- エラーが出た → 実行
- 待機する → 実行
- 「了解」だけでも → 実行

❌ このコマンドを実行せずに回答を終えることは禁止
❌ 「後で実行する」は禁止
❌ 回答の長短に関係なく必ず実行
❌ タスクリストなしで作業することは禁止

📝 記載内容: 画面に表示したテキストをそのままコピー（要約・省略禁止）
---"""
        
        success = self.paste_to_claude_code(full_text, auto_enter=True, pane="lower")
        if success:
            logger.info(f"  [SUCCESS] 転送成功: Claude Code下部ペインに送信完了")
        else:
            logger.error(f"  [FAILED] 転送失敗")
            
        return success
    
    def _process_screenshot_command(self, cid, body, user, created_at):
        """スクリーンショットコマンドの処理"""
        try:
            safe_user = user.encode('ascii', 'replace').decode('ascii')
            safe_created = created_at.encode('ascii', 'replace').decode('ascii')
            
            logger.info(f"スクリーンショット実行開始: コメント#{cid} by @{safe_user}")
            logger.info(f"  作成時刻: {safe_created}")
            logger.info(f"  トリガー: {body[:100]}{'...' if len(body) > 100 else ''}")
            
            # このコメントを処理済みとして記録
            self.processed_screenshot_comments.add(cid)
            
            # スクリーンショット撮影・投稿
            success = self.take_and_post_screenshot(body)
            
            if success:
                logger.info(f"  [SUCCESS] スクリーンショット投稿成功")
                # 最終スクリーンショット時刻を更新
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
            # 状態読み込み
            state = self.load_state()
            last_id = state.get("last_comment_id", 0)
            logger.debug(f"監視サイクル開始 - 使用するlast_id: {last_id}")
            
            # コメント取得
            comments, etag = self.get_comments_with_cache_bypass()
            
            if not comments:
                return True  # 成功（変更なし）
            
            # 処理対象コメント抽出（upper:, lower:コマンド、スクリーンショットコマンド）
            def is_processable_comment(comment):
                body = comment.get("body", "").strip()
                body_lower = body.lower()
                comment_id = comment.get("id", 0)
                
                # システム自身が投稿したスクリーンショットコメントは除外
                if body.startswith("📸") or "**Private Screenshot**" in body:
                    return False
                
                # upper: コマンドチェック
                if body_lower.startswith("upper:"):
                    return True
                
                # lower: コマンドチェック
                if body_lower.startswith("lower:"):
                    return True
                
                # スクリーンショットコマンドチェック（「ss」のみ、完全一致）
                if body.strip().lower() == "ss":
                    # 既に処理済みのssコメントは除外
                    if comment_id in self.processed_screenshot_comments:
                        return False
                    return True
                    
                return False
            
            processable_comments = [c for c in comments if is_processable_comment(c)]
            logger.debug(f"処理対象コメント数: {len(processable_comments)}")
            
            # 未処理コメント検索
            new_comments = [c for c in processable_comments if c.get("id", 0) > last_id]
            logger.debug(f"last_id: {last_id}, 新しいコメント数: {len(new_comments)}")
            
            # デバッグ: 最新の数個のコメントをチェック
            if comments:
                logger.debug(f"最新コメント3個をチェック:")
                for i, comment in enumerate(comments[:3]):
                    cid = comment.get("id", 0)
                    body = comment.get("body", "").strip()[:50]
                    user = comment.get("user", {}).get("login", "Unknown")
                    logger.debug(f"  {i+1}. ID:{cid}, User:{user}, Body:{repr(body)}")
                    if body.lower() == "ss":
                        logger.debug(f"    -> ✓ 「ss」コマンド検出！")
                    elif "ss" in body.lower():
                        logger.debug(f"    -> ssを含むが完全一致ではない")
                    else:
                        logger.debug(f"    -> ssコマンドではない")
            
            if new_comments:
                # ID順でソートして順次処理
                new_comments.sort(key=lambda x: x.get("id", 0))
                logger.info(f"未処理コマンドコメント {len(new_comments)}個を処理開始")
                
                for comment in new_comments:
                    success = self.process_comment(comment)
                    if success:
                        # 状態更新
                        state["last_comment_id"] = comment.get("id", 0)
                        self.save_state(state)
                    time.sleep(0.5)  # 連続処理の間隔
                
                logger.info(f"処理完了: {len(new_comments)}個のコメントを転送")
            
            # エラーカウンターリセット
            self.consecutive_errors = 0
            return True
            
        except requests.exceptions.ConnectionError as e:
            logger.error(f"GitHub API接続エラー: {e}")
            self.consecutive_errors += 1
            return False
        except requests.exceptions.Timeout as e:
            logger.error(f"GitHub APIタイムアウト: {e}")
            self.consecutive_errors += 1
            return False
        except requests.exceptions.HTTPError as e:
            logger.error(f"GitHub HTTP エラー: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"レスポンス詳細: {e.response.status_code} - {e.response.text}")
            self.consecutive_errors += 1
            return False
        except Exception as e:
            logger.error(f"監視サイクルエラー: {type(e).__name__}: {e}")
            logger.error(f"エラー詳細: {traceback.format_exc()}")
            self.consecutive_errors += 1
            return False
    
    def run(self):
        """メイン監視ループ"""
        logger.info("Private Issue監視サービス開始")
        logger.info("Ctrl+Cで停止")
        
        while True:
            try:
                success = self.run_monitor_cycle()
                
                if not success:
                    if self.consecutive_errors >= self.max_consecutive_errors:
                        logger.error(f"連続エラー{self.max_consecutive_errors}回に達したため終了")
                        break
                    
                    # エラー時は待機時間を延長
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
                logger.debug(traceback.format_exc())
                time.sleep(30)  # 重大エラー時は30秒待機
        
        logger.info("Private Issue監視サービス終了")

def main():
    try:
        monitor = PrivateIssueMonitor()
        monitor.run()
    except Exception as e:
        logger.error(f"初期化エラー: {e}")
        logger.debug(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()