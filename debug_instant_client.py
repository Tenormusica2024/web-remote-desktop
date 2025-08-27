#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug Instant Client - 問題特定用
"""
import socketio
import pyautogui
import base64
import io
import time

pyautogui.FAILSAFE = True

print("DEBUG INSTANT CLIENT - 開始")

sio = socketio.Client()
server_url = 'https://remote-desktop-ycqe3vmjva-uc.a.run.app'

@sio.event
def connect():
    print("✓ 接続成功！")
    print("✓ register_local_client 送信中...")
    sio.emit('register_local_client')
    print("✓ PCクライアント登録完了")
    
    print("✓ スクリーンショット取得中...")
    screenshot = pyautogui.screenshot().resize((800, 600))
    buffer = io.BytesIO()
    screenshot.save(buffer, format='JPEG', quality=70)
    img_data = base64.b64encode(buffer.getvalue()).decode()
    
    print("✓ screen_update 送信中...")
    sio.emit('screen_update', {'image': img_data})
    print("✓ スクリーンショット送信完了 - 画面表示準備完了！")
    print("=== PC クライアント準備完了 ===")

@sio.event
def disconnect():
    print("❌ 切断されました")

@sio.event
def connect_error(data):
    print(f"❌ 接続エラー: {data}")

@sio.event
def execute_command(data):
    cmd = data.get('command')
    cmd_data = data.get('data', {})
    print(f"🔧 コマンド受信: {cmd}")
    
    if cmd == 'type':
        text = cmd_data.get('text', '')
        if text:
            print(f"⌨️ テキスト入力: {text}")
            w, h = pyautogui.size()
            click_x = int(w*0.75)
            click_y = int(h*0.90)
            print(f"🖱️ クリック位置: ({click_x}, {click_y})")
            pyautogui.click(click_x, click_y)
            time.sleep(0.1)
            pyautogui.typewrite(text)
            print(f"✓ 入力完了: {text}")
            sio.emit('command_result', {'command': 'TYPE', 'success': True})
    
    elif cmd == 'key':
        key = cmd_data.get('key', '')
        if key:
            print(f"⌨️ キー押下: {key}")
            if key == 'enter':
                w, h = pyautogui.size()
                pyautogui.click(int(w*0.75), int(h*0.90))
                time.sleep(0.1)
            pyautogui.press(key)
            print(f"✓ キー実行: {key}")
            sio.emit('command_result', {'command': 'KEY', 'success': True})
    
    elif cmd == 'screenshot':
        print("📸 スクリーンショット要求")
        screenshot = pyautogui.screenshot().resize((800, 600))
        buffer = io.BytesIO()
        screenshot.save(buffer, format='JPEG', quality=70)
        img_data = base64.b64encode(buffer.getvalue()).decode()
        sio.emit('screen_update', {'image': img_data})
        print("✓ スクリーンショット送信")

@sio.event
def screenshot_request():
    print("📸 スクリーンショット要求受信")
    screenshot = pyautogui.screenshot().resize((800, 600))
    buffer = io.BytesIO()
    screenshot.save(buffer, format='JPEG', quality=70)
    img_data = base64.b64encode(buffer.getvalue()).decode()
    sio.emit('screen_update', {'image': img_data})
    print("✓ スクリーンショット応答送信")

@sio.event
def web_client_connected():
    print("🌐 Webクライアント接続検知！")
    print("📸 リロード対応スクリーンショット送信中...")
    screenshot = pyautogui.screenshot().resize((800, 600))
    buffer = io.BytesIO()
    screenshot.save(buffer, format='JPEG', quality=70)
    img_data = base64.b64encode(buffer.getvalue()).decode()
    sio.emit('screen_update', {'image': img_data})
    print("✓ リロード対応完了")

print("🔗 サーバー接続中...")
print(f"🌐 URL: {server_url}")

try:
    sio.connect(server_url, transports=['polling'], wait_timeout=10)
    print("✓ 接続確立成功！")
    print("⏳ イベント待機中...")
    sio.wait()
except KeyboardInterrupt:
    print("⏹️ ユーザーによる停止")
    sio.disconnect()
except Exception as e:
    print(f"❌ エラー発生: {e}")
    input("Enterキーを押して終了...")