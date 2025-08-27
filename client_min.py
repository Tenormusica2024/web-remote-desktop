#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最小限クライアント - 映るまでの復旧専用ライン
"""
import socketio
import pyautogui
import base64
import io
import time
import sys
try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
except ImportError:
    print("WARNING: pyperclip not installed. テキスト貼り付け機能は制限されます")
    PYPERCLIP_AVAILABLE = False

pyautogui.FAILSAFE = True

print("最小限クライアント起動")
print("復旧専用：HTTP fallback → Socket.IO")

sio = socketio.Client()

# ユーザーが指定したサーバーURL
server_url = "https://remote-desktop-2yy4vkcmia-uc.a.run.app"

@sio.event
def connect():
    print("=== 接続成功 ===")
    sio.emit('register_local_client')
    send_screenshot()
    print("初期スクリーンショット送信完了")

@sio.event 
def disconnect():
    print("サーバー切断")

def focus_claude_chat():
    """右下Claude Codeのチャット欄にフォーカスを当てる"""
    w, h = pyautogui.size()
    # 右下付近の複数座標を試行（相対座標）
    focus_points = [
        (int(w * 0.92), int(h * 0.95)),  # 右下
        (int(w * 0.88), int(h * 0.93)),  # やや左上
        (int(w * 0.94), int(h * 0.92)),  # やや右上
        (int(w * 0.90), int(h * 0.96)),  # やや左下
    ]
    
    for x, y in focus_points:
        try:
            pyautogui.click(x, y)
            time.sleep(0.1)
        except:
            continue

def focus_claude_comment():
    """右上Claude Codeのコメント欄にフォーカスを当てる"""
    w, h = pyautogui.size()
    # 右上付近の複数座標を試行（相対座標）
    focus_points = [
        (int(w * 0.95), int(h * 0.15)),  # 右上
        (int(w * 0.92), int(h * 0.18)),  # やや左下
        (int(w * 0.97), int(h * 0.12)),  # やや右上
        (int(w * 0.90), int(h * 0.20)),  # やや左下
        (int(w * 0.88), int(h * 0.16)),  # さらに左
    ]
    
    for x, y in focus_points:
        try:
            pyautogui.click(x, y)
            time.sleep(0.1)
        except:
            continue

def paste_text_to_claude(text: str, send_enter: bool, target: str = 'chat'):
    """Claude Codeにテキストを貼り付け"""
    try:
        target_name = 'コメント欄（右上）' if target == 'comment' else 'チャット欄（右下）'
        print(f"テキスト貼り付け開始: {len(text)} chars, enter={send_enter}, target={target_name}")
        
        # 1) 適切な場所にフォーカス
        if target == 'comment':
            focus_claude_comment()
        else:
            focus_claude_chat()
        time.sleep(0.2)
        
        # 2) 既存テキストをクリア
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.1)
        pyautogui.press('backspace')
        time.sleep(0.1)
        
        # 3) テキスト貼り付け
        if PYPERCLIP_AVAILABLE:
            # クリップボード経由（高速・安定）
            pyperclip.copy(text.replace('\\r\\n', '\\n'))
            time.sleep(0.1)
            pyautogui.hotkey('ctrl', 'v')
        else:
            # 直接タイピング（遅いがフォールバック）
            pyautogui.typewrite(text, interval=0.02)
        
        # 4) 必要に応じてEnter送信
        if send_enter:
            time.sleep(0.2)
            pyautogui.press('enter')
        
        print(f"テキスト貼り付け完了: {target_name}")
        
    except Exception as e:
        print(f"テキスト貼り付けエラー: {e}")

def send_screenshot():
    """スクリーンショット送信（最適化）"""
    try:
        # 高解像度・適切な縦横比で視認性向上
        screen = pyautogui.screenshot()
        original_w, original_h = screen.size
        # 16:9 縦横比で1200x675に調整（元の縦横比を保持）
        if original_w / original_h > 16/9:
            # 横長の場合は高さ基準
            new_h = 675
            new_w = int(new_h * original_w / original_h)
        else:
            # 縦長の場合は幅基準
            new_w = 1200
            new_h = int(new_w * original_h / original_w)
        screen = screen.resize((new_w, new_h))
        
        buffer = io.BytesIO()
        screen.save(buffer, format='JPEG', quality=50)
        jpeg_data = base64.b64encode(buffer.getvalue()).decode()
        
        sio.emit('screen_update', {'image': jpeg_data})
        print(f"スクリーンショット送信: {len(jpeg_data)} bytes")
        return True
    except Exception as e:
        print(f"スクリーンショットエラー: {e}")
        return False

# テキスト貼り付けイベント
@sio.on('paste_text')
def on_paste_text(data):
    """サーバーからのテキスト貼り付け指示を処理"""
    try:
        text = (data or {}).get('text', '').strip()
        send_enter = bool((data or {}).get('send_enter', False))
        target = (data or {}).get('target', 'chat')
        if text:
            paste_text_to_claude(text, send_enter, target)
    except Exception as e:
        print(f"paste_text イベントエラー: {e}")

# その他イベント処理
@sio.on('*')
def catch_all(event, *args):
    if event != 'paste_text':  # ログ量を減らす
        print(f"イベント: {event}")

print(f"接続先: {server_url}")

try:
    # polling only（プロキシ対応）
    sio.connect(server_url, transports=['polling'], wait_timeout=10)
    print("接続成功！")
    
    # 3秒間隔でスクリーンショット送信
    while True:
        time.sleep(3)
        send_screenshot()
        
except KeyboardInterrupt:
    print("\nユーザー停止")
    sio.disconnect()
except Exception as e:
    print(f"接続エラー: {e}")
    input("Enterで終了...")