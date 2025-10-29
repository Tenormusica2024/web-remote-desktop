#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Private Issue Monitor + Screenshot Uploader 統合起動スクリプト (Python版)
2つのサービスを同時に起動・管理
"""

import os
import sys
import time
import subprocess
import signal
from pathlib import Path

# スクリプトディレクトリに移動
SCRIPT_DIR = Path(__file__).resolve().parent
os.chdir(SCRIPT_DIR)

print("=" * 60)
print("Private Issue Monitor + Screenshot System")
print("=" * 60)
print()

# 必要なファイル確認
required_files = [
    ".env_private",
    "private_issue_monitor_service.py",
    "pc-snap-uploader-private.py",
    ".gh_issue_to_claude_coords_private_new.json"
]

for file in required_files:
    if not Path(file).exists():
        print(f"[ERROR] 必要なファイルが見つかりません: {file}")
        sys.exit(1)

print("[INFO] 必要なファイル確認: OK")
print()

# Pythonライブラリ確認
required_modules = ["pyautogui", "pyperclip", "keyboard", "requests"]
missing_modules = []

for module in required_modules:
    try:
        __import__(module)
    except ImportError:
        missing_modules.append(module)

if missing_modules:
    print(f"[WARNING] 不足しているライブラリ: {', '.join(missing_modules)}")
    print("[INFO] インストールを試行中...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_modules)
        print("[INFO] ライブラリインストール完了")
    except subprocess.CalledProcessError:
        print("[ERROR] ライブラリのインストールに失敗しました")
        sys.exit(1)

print("[INFO] ライブラリ確認: OK")
print()

# サブプロセス格納用
processes = []

def signal_handler(sig, frame):
    """Ctrl+C ハンドラ"""
    print("\n[INFO] 停止シグナルを受信しました")
    print("[INFO] サービスを停止中...")
    
    for proc in processes:
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
    
    print("[INFO] すべてのサービスを停止しました")
    sys.exit(0)

# シグナルハンドラ登録
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# サービス起動
print("=" * 60)
print("2つのサービスを起動します:")
print("1. Private Issue Monitor Service")
print("2. Screenshot Uploader (Hotkey: Ctrl+Alt+F12)")
print("=" * 60)
print()
print("[!] 停止するには Ctrl+C を押してください")
print()

try:
    # Monitor Service起動
    print("[INFO] Private Issue Monitor Service を起動中...")
    monitor_proc = subprocess.Popen(
        [sys.executable, "private_issue_monitor_service.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    processes.append(monitor_proc)
    time.sleep(2)
    
    # Screenshot Uploader起動
    print("[INFO] Screenshot Uploader を起動中...")
    uploader_proc = subprocess.Popen(
        [sys.executable, "pc-snap-uploader-private.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    processes.append(uploader_proc)
    time.sleep(2)
    
    print()
    print("=" * 60)
    print("[SUCCESS] 両サービスが起動しました")
    print("=" * 60)
    print()
    print("[Monitor] Private Issue Monitor Service - 実行中")
    print("          - GitHub Issue のコメントを監視")
    print('          - "upper:" コマンド → Claude Code上部ペイン')
    print('          - "lower:" コマンド → Claude Code下部ペイン')
    print('          - "ss" コマンド → スクリーンショット撮影・投稿')
    print()
    print("[Uploader] Screenshot Uploader - 実行中")
    print("           - ホットキー: Ctrl+Alt+F12")
    print("           - スクリーンショット即座撮影・アップロード")
    print("           - Private リポジトリに投稿")
    print()
    print("ログファイル:")
    print("- private_issue_monitor.log (Monitor)")
    print("- Uploaderログはコンソール出力")
    print()
    
    # 両プロセスが実行中である限りループ
    while True:
        # プロセス生存確認
        monitor_alive = monitor_proc.poll() is None
        uploader_alive = uploader_proc.poll() is None
        
        if not monitor_alive:
            print("[ERROR] Private Issue Monitor が停止しました")
            break
        
        if not uploader_alive:
            print("[ERROR] Screenshot Uploader が停止しました")
            break
        
        # ログ出力（あれば）
        try:
            # Monitor のログ
            if monitor_alive:
                line = monitor_proc.stdout.readline()
                if line:
                    print(f"[Monitor] {line.strip()}")
            
            # Uploader のログ
            if uploader_alive:
                line = uploader_proc.stdout.readline()
                if line:
                    print(f"[Uploader] {line.strip()}")
        except:
            pass
        
        time.sleep(0.1)

except KeyboardInterrupt:
    print("\n[INFO] ユーザーによる停止要求")
except Exception as e:
    print(f"[ERROR] 予期しないエラー: {e}")
finally:
    # クリーンアップ
    print("[INFO] サービスを停止中...")
    for proc in processes:
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        except:
            pass
    
    print("[INFO] すべてのサービスを停止しました")
