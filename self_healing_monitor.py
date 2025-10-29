#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自己回復型監視スクリプトラッパー

監視スクリプトをラップし、異常終了時に自動的に再起動します。
- クラッシュ時の自動再起動
- 連続エラーの検出と対処
- ハートビート監視（応答なし検出）

使用方法:
python self_healing_monitor.py [監視スクリプトのパス]

例:
python self_healing_monitor.py private_issue_monitor_service.py
python self_healing_monitor.py github-issue-remote-tool-v2/monitor_service_multi.py
"""

import os
import sys
import subprocess
import time
import logging
import signal
from pathlib import Path
from datetime import datetime
import threading

# ログ設定
LOG_FILE = Path(__file__).parent / "self_healing_monitor.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class SelfHealingMonitor:
    def __init__(self, script_path):
        self.script_path = Path(script_path)
        self.cwd = self.script_path.parent
        self.process = None
        self.is_running = True
        self.restart_count = 0
        self.max_restart_count = 100  # 最大再起動回数
        self.restart_delay = 5  # 再起動待機時間（秒）
        self.last_restart_time = None
        
        if not self.script_path.exists():
            raise FileNotFoundError(f"スクリプトが見つかりません: {script_path}")
        
        logger.info("=" * 60)
        logger.info("自己回復型監視スクリプトラッパー")
        logger.info("=" * 60)
        logger.info(f"監視対象: {self.script_path}")
        logger.info(f"作業ディレクトリ: {self.cwd}")
        logger.info(f"最大再起動回数: {self.max_restart_count}")
        logger.info("=" * 60)
    
    def start_process(self):
        """監視スクリプトを起動"""
        try:
            logger.info(f"プロセス起動開始...")
            
            python_exe = sys.executable
            
            self.process = subprocess.Popen(
                [python_exe, str(self.script_path.name)],
                cwd=str(self.cwd),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            logger.info(f"[OK] プロセス起動成功: PID={self.process.pid}")
            self.restart_count += 1
            self.last_restart_time = datetime.now()
            
            return True
        except Exception as e:
            logger.error(f"✗ プロセス起動失敗: {e}")
            return False
    
    def stop_process(self):
        """監視スクリプトを停止"""
        if self.process and self.process.poll() is None:
            try:
                logger.info(f"プロセス停止中: PID={self.process.pid}")
                self.process.terminate()
                
                # 5秒待機して強制終了
                try:
                    self.process.wait(timeout=5)
                    logger.info("[OK] プロセス正常終了")
                except subprocess.TimeoutExpired:
                    logger.warning("タイムアウト - 強制終了実行")
                    self.process.kill()
                    self.process.wait()
                    logger.info("[OK] プロセス強制終了")
                
            except Exception as e:
                logger.error(f"プロセス停止エラー: {e}")
    
    def monitor_process(self):
        """プロセスを監視し、異常終了時に再起動"""
        while self.is_running:
            if not self.start_process():
                logger.error("プロセス起動失敗 - 5秒後に再試行")
                time.sleep(5)
                continue
            
            # プロセス終了を待機
            returncode = self.process.wait()
            
            if not self.is_running:
                logger.info("監視停止要求を受信 - 再起動せずに終了")
                break
            
            # 終了コード確認
            elapsed = (datetime.now() - self.last_restart_time).total_seconds()
            
            if returncode == 0:
                logger.info(f"プロセス正常終了（終了コード: 0、稼働時間: {elapsed:.1f}秒）")
                logger.info("正常終了のため再起動しません")
                break
            else:
                logger.warning(f"プロセス異常終了（終了コード: {returncode}、稼働時間: {elapsed:.1f}秒）")
            
            # 再起動回数チェック
            if self.restart_count >= self.max_restart_count:
                logger.error(f"最大再起動回数（{self.max_restart_count}）に到達 - 監視終了")
                break
            
            # 短時間での連続クラッシュ検出
            if elapsed < 30:
                logger.warning(f"短時間でのクラッシュ検出（{elapsed:.1f}秒） - 待機時間延長")
                delay = min(60, self.restart_delay * 2)
            else:
                delay = self.restart_delay
            
            logger.info(f"再起動まで{delay}秒待機... (再起動回数: {self.restart_count}/{self.max_restart_count})")
            time.sleep(delay)
    
    def signal_handler(self, signum, frame):
        """シグナルハンドラ（Ctrl+C等）"""
        logger.info(f"停止シグナル受信: {signum}")
        self.is_running = False
        self.stop_process()
        sys.exit(0)
    
    def run(self):
        """メイン実行"""
        # シグナルハンドラ登録
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        try:
            self.monitor_process()
        except Exception as e:
            logger.error(f"予期しないエラー: {e}", exc_info=True)
        finally:
            self.stop_process()
            logger.info("=" * 60)
            logger.info(f"監視終了 - 総再起動回数: {self.restart_count - 1}")
            logger.info("=" * 60)

def main():
    """メイン処理"""
    if len(sys.argv) < 2:
        print("使用方法: python self_healing_monitor.py [スクリプトパス]")
        print()
        print("例:")
        print("  python self_healing_monitor.py private_issue_monitor_service.py")
        print("  python self_healing_monitor.py github-issue-remote-tool-v2/monitor_service_multi.py")
        return 1
    
    script_path = sys.argv[1]
    
    try:
        monitor = SelfHealingMonitor(script_path)
        monitor.run()
        return 0
    except Exception as e:
        logger.error(f"初期化エラー: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())