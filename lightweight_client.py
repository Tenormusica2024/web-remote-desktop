#!/usr/bin/env python3
"""
Lightweight Client - 軽量版（画像最適化済み）
"""
import socketio
import pyautogui
import base64
import io
import time
import sys

pyautogui.FAILSAFE = True

print("LIGHTWEIGHT CLIENT STARTING")
print("Optimized for stable screen sharing")

sio = socketio.Client(logger=True, engineio_logger=True)
server_url = 'https://remote-desktop-2yy4vkcmia-uc.a.run.app'

@sio.event
def connect():
    print("\n=== CONNECTION ESTABLISHED ===")
    print("Registering as local client...")
    sio.emit('register_local_client')
    
    # Send initial optimized screenshot
    print("Taking optimized screenshot...")
    send_optimized_screenshot()
    print("=== LIGHTWEIGHT CLIENT READY ===")

@sio.event
def disconnect():
    print("DISCONNECTED FROM SERVER")

@sio.event
def connect_error(data):
    print(f"CONNECTION ERROR: {data}")

@sio.event
def execute_command(data):
    print(f"COMMAND RECEIVED: {data}")
    cmd = data.get('command')
    cmd_data = data.get('data', {})
    
    if cmd == 'type':
        text = cmd_data.get('text', '')
        if text:
            print(f"TYPING: '{text}'")
            pyautogui.typewrite(text, interval=0.05)
            sio.emit('command_result', {'command': 'TYPE', 'success': True})
    
    elif cmd == 'key':
        key = cmd_data.get('key', '')
        if key:
            print(f"PRESSING KEY: '{key}'")
            pyautogui.press(key)
            sio.emit('command_result', {'command': 'KEY', 'success': True})

def send_optimized_screenshot():
    """最適化されたスクリーンショット送信"""
    try:
        # 大幅に解像度とサイズを削減
        screenshot = pyautogui.screenshot()
        print(f"Original size: {screenshot.size}")
        
        # 400x300に縮小（データサイズ大幅削減）
        screenshot = screenshot.resize((400, 300))
        print("Resized to 400x300")
        
        # 低品質JPEG（データサイズ最小化）
        buffer = io.BytesIO()
        screenshot.save(buffer, format='JPEG', quality=40)
        img_data = base64.b64encode(buffer.getvalue()).decode()
        
        print(f"Optimized data size: {len(img_data)} bytes (~{len(img_data)/1024:.1f}KB)")
        
        if len(img_data) > 100000:  # 100KB制限
            print("WARNING: Image still too large, reducing further...")
            screenshot = screenshot.resize((300, 225))
            buffer = io.BytesIO()
            screenshot.save(buffer, format='JPEG', quality=30)
            img_data = base64.b64encode(buffer.getvalue()).decode()
            print(f"Ultra-compressed size: {len(img_data)} bytes")
        
        sio.emit('screen_update', {'image': img_data})
        print("OPTIMIZED SCREENSHOT SENT")
        return True
        
    except Exception as e:
        print(f"SCREENSHOT ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

@sio.event
def screenshot_request():
    print("SCREENSHOT REQUEST RECEIVED")
    send_optimized_screenshot()

@sio.event
def web_client_connected():
    print("\n=== WEB CLIENT CONNECTED ===")
    print("Sending optimized screenshot...")
    
    # 1回だけ送信（安定性重視）
    if send_optimized_screenshot():
        print("SCREENSHOT SENT TO WEB CLIENT")
    
    print("=== WEB CLIENT RESPONSE COMPLETE ===")

@sio.event
def local_client_disconnected():
    print("RECONNECTION REQUESTED")
    time.sleep(2)
    sio.emit('register_local_client')
    send_optimized_screenshot()

# イベントキャッチ
@sio.on('*')
def catch_all(event, *args):
    print(f"EVENT: {event}")

print(f"CONNECTING TO: {server_url}")
print("Transport: polling (optimized)")

try:
    print("Attempting stable connection...")
    sio.connect(server_url, transports=['polling'], wait_timeout=10)
    print("CONNECTION SUCCESS!")
    
    # 高頻度スクリーンショット更新（3秒間隔）
    while True:
        time.sleep(3)
        print("Sending periodic screenshot...")
        send_optimized_screenshot()
        
except KeyboardInterrupt:
    print("\nSTOPPED BY USER")
    sio.disconnect()
except Exception as e:
    print(f"CONNECTION FAILED: {e}")
    import traceback
    traceback.print_exc()
    input("Press Enter to exit...")