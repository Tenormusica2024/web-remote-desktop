#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run system test - process pending comments
"""
import os, sys, time, json, datetime
from pathlib import Path
import requests

# Set environment variables
os.environ['GH_REPO'] = 'Tenormusica2024/web-remote-desktop'
os.environ['GH_ISSUE'] = '3'
os.environ['GH_TOKEN'] = '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'
os.environ['POLL_SEC'] = '2'  # Faster for testing
os.environ['DEFAULT_PANE'] = 'lower'
os.environ['ONLY_AUTHOR'] = 'Tenormusica2024'

def run_limited_test():
    """Run system for limited time to process pending comments"""
    print("=== GitHub Issue to Claude Code System - テスト実行 ===")
    print(f"開始時刻: {datetime.datetime.now().strftime('%H:%M:%S')}")
    print("処理対象: 未処理コメント")
    print("実行時間: 30秒間")
    print("=" * 50)
    
    # Import main system
    from gh_issue_to_claude_paste import main, parse_pane_and_text
    
    # Show what we expect to process
    session = requests.Session()
    session.headers.update({
        'Authorization': f'Bearer {os.environ["GH_TOKEN"]}',
        'Accept': 'application/vnd.github+json',
    })
    
    url = 'https://api.github.com/repos/Tenormusica2024/web-remote-desktop/issues/3/comments?per_page=5'
    r = session.get(url)
    
    if r.status_code == 200:
        comments = r.json()
        print(f"処理予定コメント {len(comments)} 件:")
        for c in comments:
            cid = c.get('id', 0)
            body = c.get('body', '')
            pane, text, no_enter = parse_pane_and_text(body)
            enter_info = "Enter無し" if no_enter else "自動Enter"
            print(f"  ID {cid}: {pane}ペイン, {len(text)}文字, {enter_info}")
            print(f"    → {text[:60]}...")
        print()
    
    # Override main function to limit execution time
    original_main = main
    
    def limited_main():
        import signal
        def timeout_handler(signum, frame):
            print(f"\n[{datetime.datetime.now().strftime('%H:%M:%S')}] テスト終了 (30秒経過)")
            print("システムを停止します...")
            sys.exit(0)
        
        # Set timeout for 30 seconds
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(30)
        
        try:
            original_main()
        except KeyboardInterrupt:
            print("\n手動停止しました")
        except SystemExit:
            print("タイムアウトによる停止")
        finally:
            signal.alarm(0)  # Cancel alarm
    
    # Run limited test
    print("システム開始中...")
    limited_main()

if __name__ == "__main__":
    try:
        run_limited_test()
    except Exception as e:
        print(f"エラー: {e}")
        print("手動でシステムを実行してください:")
        print("1. calibrate_system.bat (座標設定)")
        print("2. start_remote_system.bat (システム開始)")