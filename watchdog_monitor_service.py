#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
監視スクリプトWatchdog（監視・自動再起動）

定期的に監視スクリプトのプロセス存在を確認し、
停止していた場合は自動的に再起動します。

使用方法:
1. Windowsタスクスケジューラで5分間隔実行
2. または手動で定期実行
"""

import os
import sys
import subprocess
import psutil
import logging
from pathlib import Path
from datetime import datetime

# ログ設定
LOG_FILE = Path(__file__).parent / "watchdog_monitor.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8')
        # logging.StreamHandler(sys.stdout)  # コンソール表示を無効化
    ]
)
logger = logging.getLogger(__name__)

# 監視対象スクリプト設定
MONITOR_SCRIPTS = [
    {
        "name": "Private Issue Monitor",
        "script": "private_issue_monitor_service.py",
        "cwd": Path(__file__).parent,
        "enabled": True
    },
    {
        "name": "Multi Issue Monitor (v2)",
        "script": "github-issue-remote-tool-v2/monitor_service_multi.py",
        "cwd": Path(__file__).parent,
        "enabled": False  # 配布版使用時はTrueに変更
    }
]

def is_process_running(script_name):
    """指定されたPythonスクリプトが実行中か確認"""
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] and 'python' in proc.info['name'].lower():
                    cmdline = proc.info.get('cmdline')
                    if cmdline and any(script_name in arg for arg in cmdline):
                        logger.debug(f"プロセス検出: PID={proc.info['pid']}, cmdline={cmdline}")
                        return True, proc.info['pid']
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False, None
    except Exception as e:
        logger.error(f"プロセス確認エラー: {e}")
        return False, None

def start_monitor_service(script_path, cwd):
    """監視サービスを起動"""
    try:
        logger.info(f"監視サービス起動開始: {script_path}")
        
        # Pythonインタプリタのパスを取得
        python_exe = sys.executable
        
        # バックグラウンドプロセスとして起動
        if os.name == 'nt':  # Windows
            # Windowsではサブプロセスを完全に独立させる
            DETACHED_PROCESS = 0x00000008
            CREATE_NO_WINDOW = 0x08000000
            
            process = subprocess.Popen(
                [python_exe, str(script_path)],
                cwd=str(cwd),
                creationflags=DETACHED_PROCESS | CREATE_NO_WINDOW,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL
            )
            
            logger.info(f"起動成功: PID={process.pid}")
            return True
        else:
            # Linux/Mac
            process = subprocess.Popen(
                [python_exe, str(script_path)],
                cwd=str(cwd),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                start_new_session=True
            )
            
            logger.info(f"起動成功: PID={process.pid}")
            return True
            
    except Exception as e:
        logger.error(f"起動エラー: {e}")
        return False

def check_and_restart_services():
    """全監視サービスをチェックし、必要なら再起動"""
    logger.info("=" * 60)
    logger.info("Watchdog Monitor Service - 定期チェック開始")
    logger.info(f"チェック時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    restart_count = 0
    
    for config in MONITOR_SCRIPTS:
        if not config.get("enabled", False):
            logger.debug(f"スキップ（無効化済み）: {config['name']}")
            continue
        
        script_name = config["script"]
        service_name = config["name"]
        script_path = config["cwd"] / script_name
        
        logger.info(f"確認中: {service_name} ({script_name})")
        
        # スクリプトファイルの存在確認
        if not script_path.exists():
            logger.warning(f"スクリプトファイルが見つかりません: {script_path}")
            continue
        
        # プロセス実行確認
        is_running, pid = is_process_running(script_name)
        
        if is_running:
            logger.info(f"[OK] 実行中: PID={pid}")
        else:
            logger.warning(f"[STOP] 停止検出: {service_name}")
            logger.info(f"自動再起動を試行...")
            
            if start_monitor_service(script_path, config["cwd"]):
                logger.info(f"[OK] 再起動成功: {service_name}")
                restart_count += 1
            else:
                logger.error(f"[FAIL] 再起動失敗: {service_name}")
    
    logger.info("=" * 60)
    logger.info(f"チェック完了 - 再起動数: {restart_count}")
    logger.info("=" * 60)
    
    return restart_count

def main():
    """メイン処理"""
    try:
        restart_count = check_and_restart_services()
        
        if restart_count > 0:
            print(f"[OK] {restart_count}個の監視サービスを再起動しました")
        else:
            print("[OK] すべての監視サービスが正常稼働中です")
        
        return 0
    except Exception as e:
        logger.error(f"予期しないエラー: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())