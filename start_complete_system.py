#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Claude Code 完全リモート制御システム起動スクリプト
- スクリーンショットシステム (Issue #1)
- コメント→Claude Code システム (Issue #3)
両方を同時起動
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def set_environment_variables():
    """環境変数を設定"""
    env_vars = {
        "GH_REPO": "Tenormusica2024/web-remote-desktop",
        "GH_ISSUE": "3",  # リモート制御用
        "GH_TOKEN": "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",
        "POLL_SEC": "5",
        "DEFAULT_PANE": "lower",
        "ONLY_AUTHOR": "Tenormusica2024"
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
    
    print("✅ Environment variables set")

def check_calibration():
    """キャリブレーション済みかチェック"""
    coords_file = Path(".gh_issue_to_claude_coords.json")
    if not coords_file.exists():
        print("❌ キャリブレーションが必要です")
        print("次のコマンドを実行してください:")
        print("   python gh_issue_to_claude_paste.py --calibrate")
        return False
    print("✅ キャリブレーション済み")
    return True

def start_screenshot_system():
    """スクリーンショットシステムを開始"""
    try:
        print("🖼️ Starting screenshot system (Issue #1)...")
        screenshot_process = subprocess.Popen([
            sys.executable, "remote-monitor.py"
        ], creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0)
        print(f"   PID: {screenshot_process.pid}")
        return screenshot_process
    except Exception as e:
        print(f"❌ Screenshot system failed: {e}")
        return None

def start_remote_control_system():
    """リモート制御システムを開始"""
    try:
        print("⌨️ Starting remote control system (Issue #3)...")
        remote_process = subprocess.Popen([
            sys.executable, "gh_issue_to_claude_paste.py"
        ], creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0)
        print(f"   PID: {remote_process.pid}")
        return remote_process
    except Exception as e:
        print(f"❌ Remote control system failed: {e}")
        return None

def main():
    print("=" * 50)
    print("  Claude Code Complete Remote Control System")
    print("=" * 50)
    print()
    
    # 環境変数設定
    set_environment_variables()
    
    # キャリブレーションチェック
    if not check_calibration():
        return
    
    print()
    print("🚀 Starting both systems...")
    print()
    
    # 両システムを起動
    screenshot_proc = start_screenshot_system()
    time.sleep(2)  # 少し待機
    remote_proc = start_remote_control_system()
    
    if screenshot_proc and remote_proc:
        print()
        print("✅ Both systems started successfully!")
        print()
        print("📖 Usage:")
        print("   Issue #1: Post 'ss' in title → Screenshot")
        print("   Issue #3: Post 'upper: text' or 'lower: text' → Send to Claude Code")
        print()
        print("🔗 GitHub Issues:")
        print("   Screenshot: https://github.com/Tenormusica2024/web-remote-desktop/issues/1")
        print("   Remote Control: https://github.com/Tenormusica2024/web-remote-desktop/issues/3")
        print()
        print("Press Ctrl+C to stop both systems...")
        
        try:
            # 両プロセスの終了を待機
            while screenshot_proc.poll() is None or remote_proc.poll() is None:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping systems...")
            if screenshot_proc.poll() is None:
                screenshot_proc.terminate()
            if remote_proc.poll() is None:
                remote_proc.terminate()
            print("✅ Systems stopped")
    else:
        print("❌ Failed to start one or both systems")
        if screenshot_proc and screenshot_proc.poll() is None:
            screenshot_proc.terminate()
        if remote_proc and remote_proc.poll() is None:
            remote_proc.terminate()

if __name__ == "__main__":
    main()