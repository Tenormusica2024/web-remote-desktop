#!/usr/bin/env python3
"""
Final Stable Client - 最終安定版 (catch_allエラー修正済み)
"""
import socketio
import pyautogui
import base64
import io
import time
import sys

pyautogui.FAILSAFE = True

print("FINAL STABLE CLIENT STARTING")
print(f"Python version: {sys.version}")

sio = socketio.Client(logger=True, engineio_logger=True)
server_url = 'https://remote-desktop-2yy4vkcmia-uc.a.run.app'

@sio.event
def connect():
    print("\n=== CONNECTION ESTABLISHED ===")
    print("Emitting register_local_client...")
    sio.emit('register_local_client')
    print("Registration event sent")
    
    print("Taking initial screenshot...")
    try:
        screenshot = pyautogui.screenshot()
        print(f"Screenshot taken: {screenshot.size}")
        
        screenshot = screenshot.resize((800, 600))
        print("Screenshot resized to 800x600")
        
        buffer = io.BytesIO()
        screenshot.save(buffer, format='JPEG', quality=70)
        img_data = base64.b64encode(buffer.getvalue()).decode()
        print(f"Screenshot encoded, data length: {len(img_data)}")
        
        print("Emitting screen_update...")
        sio.emit('screen_update', {'image': img_data})
        print("INITIAL SCREEN UPDATE SENT!")
        
    except Exception as e:
        print(f"SCREENSHOT ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    print("=== PC CLIENT READY ===")

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
            print(f"TYPING TEXT: '{text}'")
            w, h = pyautogui.size()
            click_x = int(w*0.75)
            click_y = int(h*0.91)
            print(f"Clicking at ({click_x}, {click_y})")
            pyautogui.click(click_x, click_y)
            time.sleep(0.2)
            
            print("Clearing existing text...")
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.1)
            
            print("Typing text...")
            pyautogui.typewrite(text, interval=0.03)
            print(f"TEXT TYPED: '{text}'")
            sio.emit('command_result', {'command': 'TYPE', 'success': True})
    
    elif cmd == 'key':
        key = cmd_data.get('key', '')
        if key:
            print(f"PRESSING KEY: '{key}'")
            if key.lower() == 'enter':
                w, h = pyautogui.size()
                pyautogui.click(int(w*0.75), int(h*0.91))
                time.sleep(0.1)
            pyautogui.press(key)
            print(f"KEY PRESSED: '{key}'")
            sio.emit('command_result', {'command': 'KEY', 'success': True})
    
    elif cmd == 'screenshot':
        print("MANUAL SCREENSHOT REQUEST")
        send_screenshot()

def send_screenshot():
    """スクリーンショット送信処理"""
    try:
        screenshot = pyautogui.screenshot().resize((800, 600))
        buffer = io.BytesIO()
        screenshot.save(buffer, format='JPEG', quality=70)
        img_data = base64.b64encode(buffer.getvalue()).decode()
        sio.emit('screen_update', {'image': img_data})
        print("SCREENSHOT SENT")
        return True
    except Exception as e:
        print(f"SCREENSHOT ERROR: {e}")
        return False

@sio.event
def screenshot_request():
    print("SCREENSHOT REQUEST EVENT RECEIVED")
    send_screenshot()

@sio.event
def web_client_connected():
    print("\n=== WEB CLIENT CONNECTED EVENT ===")
    print("Smartphone client connected, sending fresh screenshot...")
    
    try:
        # 即座に送信
        if send_screenshot():
            print("FRESH SCREENSHOT SENT!")
        
        # 追加で2回送信（確実性向上）
        for i in range(2):
            time.sleep(0.5)
            if send_screenshot():
                print(f"ADDITIONAL SCREENSHOT {i+1} SENT")
        
    except Exception as e:
        print(f"WEB CLIENT CONNECT RESPONSE ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    print("=== WEB CLIENT CONNECT RESPONSE COMPLETE ===")

@sio.event
def local_client_disconnected():
    print("LOCAL CLIENT DISCONNECTED EVENT - ATTEMPTING RECONNECT")
    time.sleep(1)
    sio.emit('register_local_client')
    send_screenshot()

# その他のイベント処理 (catch_all修正)
@sio.on('*')
def catch_all(event, *args):
    print(f"UNKNOWN EVENT: {event}, ARGS: {args}")

print(f"CONNECTING TO: {server_url}")
print("Transport: polling only")

try:
    print("Attempting connection...")
    sio.connect(server_url, transports=['polling'], wait_timeout=15)
    print("CONNECTION SUCCESS!")
    print("Waiting for events...")
    sio.wait()
    
except KeyboardInterrupt:
    print("\nSTOPPED BY USER")
    sio.disconnect()
except Exception as e:
    print(f"CONNECTION FAILED: {e}")
    import traceback
    traceback.print_exc()
    input("Press Enter to exit...")