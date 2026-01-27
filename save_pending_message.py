#!/usr/bin/env python3
"""
未送信メッセージ保存ヘルパー
Claude Codeが送信しようとしていたメッセージを保存する
"""

import sys
from pathlib import Path

def save_pending_message(message):
    """未送信メッセージをファイルに保存"""
    try:
        file_path = Path(__file__).parent / "pending_claude_message.txt"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(message)
        print(f"未送信メッセージを保存しました（{len(message)}文字）")
        return True
    except Exception as e:
        print(f"保存エラー: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # コマンドライン引数からメッセージを取得
        message = " ".join(sys.argv[1:])
    else:
        # 標準入力から読み取り
        message = sys.stdin.read()
    
    save_pending_message(message)