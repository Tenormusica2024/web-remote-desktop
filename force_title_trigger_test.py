#!/usr/bin/env python3
"""
タイトル変更によるスクリーンショットトリガーのテスト
- GitHub APIのキャッシュ問題を回避するため手動でスクリーンショットを実行
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# パスを追加してremote-monitorモジュールをインポート
sys.path.append(str(Path(__file__).resolve().parent))

# 設定読み込み
ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env_private", override=True)

def manual_title_trigger_test():
    """手動でタイトル検知によるスクリーンショットをテスト"""
    
    try:
        # remote-monitor_private_new.py からexecute_screenshot_command関数をインポート
        from remote_monitor_private_new import execute_screenshot_command
        
        print("=== Manual Title Screenshot Trigger Test ===")
        print("Testing screenshot command execution via title trigger...")
        
        # テスト用のコマンドオブジェクトを作成（ユーザーのタイトル変更をシミュレート）
        test_cmd = {
            "id": "manual_title_test_001",
            "author": "Tenormusica2024",
            "body": "Manual title trigger test: ss remote working test1",
            "created_at": "2025-09-17T21:25:00Z",
            "url": "https://github.com/Tenormusica2024/Private/issues/1"
        }
        
        print(f"Simulating title change: '{test_cmd['body']}'")
        print("Executing screenshot command...")
        
        # スクリーンショットコマンドを実行
        execute_screenshot_command(test_cmd)
        
        print("✅ Manual title trigger test completed successfully!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Could not import execute_screenshot_command from remote-monitor script")
        
    except Exception as e:
        print(f"❌ Execution error: {e}")

if __name__ == "__main__":
    manual_title_trigger_test()