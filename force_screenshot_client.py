#!/usr/bin/env python3
"""
Force Screenshot Client - 強制スクリーンショット送信
"""
import socketio
import pyautogui
import base64
import io
import time
import threading

pyautogui.FAILSAFE = True

print("FORCE SCREENSHOT CLIENT STARTING")

sio = socketio.Client()
server_url = 'https://remote-desktop-ycqe3vmjva-uc.a.run.app'

def force_send_screenshot():
    """強制スクリーンショット送信"""
    try:
        print("TAKING SCREENSHOT...")
        screenshot = pyautogui.screenshot()
        screenshot = screenshot.resize((800, 600))
        
        buffer = io.BytesIO()
        screenshot.save(buffer, format='JPEG', quality=70)
        img_data = base64.b64encode(buffer.getvalue()).decode()
        
        print("SENDING SCREENSHOT...")
        sio.emit('screen_update', {'image': img_data})
        print("SCREENSHOT SENT!")
        return True
    except Exception as e:
        print(f"SCREENSHOT ERROR: {e}")
        return False

def continuous_screenshot():
    """継続的スクリーンショット送信"""
    while True:
        time.sleep(3)  # 3秒毎
        if sio.connected:
            force_send_screenshot()

@sio.event
def connect():
    print("CONNECTED TO SERVER!")
    print("REGISTERING PC CLIENT...")
    sio.emit('register_local_client')
    
    # 即座にスクリーンショット送信
    time.sleep(0.5)
    force_send_screenshot()
    
    # 追加で3回送信（確実性向上）
    for i in range(3):
        time.sleep(0.5)
        print(f"ADDITIONAL SCREENSHOT {i+1}...")
        force_send_screenshot()
    
    print("=== PC CLIENT READY ===")

@sio.event
def disconnect():
    print("DISCONNECTED FROM SERVER")

@sio.event
def connect_error(data):
    print(f"CONNECTION ERROR: {data}")

@sio.event
def execute_command(data):
    cmd = data.get('command')
    cmd_data = data.get('data', {})
    print(f"COMMAND: {cmd}")
    
    if cmd == 'type':
        text = cmd_data.get('text', '')
        if text:
            print(f"TYPING: {text}")
            w, h = pyautogui.size()
            pyautogui.click(int(w*0.75), int(h*0.91))
            time.sleep(0.2)
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.1)
            pyautogui.typewrite(text, interval=0.03)
            print(f"TYPED: {text}")
            sio.emit('command_result', {'command': 'TYPE', 'success': True})
    
    elif cmd == 'key':
        key = cmd_data.get('key', '')
        if key:
            print(f"KEY: {key}")
            if key.lower() == 'enter':
                w, h = pyautogui.size()
                pyautogui.click(int(w*0.75), int(h*0.91))
                time.sleep(0.1)
            pyautogui.press(key)
            print(f"PRESSED: {key}")
            sio.emit('command_result', {'command': 'KEY', 'success': True})
    
    elif cmd == 'screenshot':
        print("MANUAL SCREENSHOT REQUEST")
        force_send_screenshot()

@sio.event
def screenshot_request():
    print("SCREENSHOT REQUEST EVENT")
    force_send_screenshot()

@sio.event
def web_client_connected():
    print("WEB CLIENT RELOAD DETECTED!")
    
    # リロード時に5回連続でスクリーンショット送信
    for i in range(5):
        print(f"RELOAD SCREENSHOT {i+1}...")
        force_send_screenshot()
        time.sleep(0.3)
    
    print("RELOAD RESPONSE COMPLETE")

# 継続的スクリーンショット送信を開始
screenshot_thread = threading.Thread(target=continuous_screenshot, daemon=True)

print("CONNECTING TO CLOUD RUN...")
print(f"URL: {server_url}")

try:
    sio.connect(server_url, transports=['polling'], wait_timeout=15)
    print("CONNECTION ESTABLISHED!")
    
    # 継続的スクリーンショット開始
    screenshot_thread.start()
    print("CONTINUOUS SCREENSHOT STARTED")
    
    print("WAITING FOR EVENTS...")
    sio.wait()
    
except KeyboardInterrupt:
    print("STOPPED BY USER")
    sio.disconnect()
except Exception as e:
    print(f"CONNECTION ERROR: {e}")
    input("Press Enter to exit...")