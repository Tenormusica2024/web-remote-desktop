#!/usr/bin/env python3
"""
Verbose Debug Client - 詳細ログ付き問題特定用
"""
import socketio
import pyautogui
import base64
import io
import time
import sys

pyautogui.FAILSAFE = True

print("VERBOSE DEBUG CLIENT STARTING")
print(f"Python version: {sys.version}")

sio = socketio.Client(logger=True, engineio_logger=True)
server_url = 'https://remote-desktop-ycqe3vmjva-uc.a.run.app'

@sio.event
def connect():
    print("\n=== CONNECTION ESTABLISHED ===")
    print("Emitting register_local_client...")
    sio.emit('register_local_client')
    print("Registration event sent")
    
    print("Taking screenshot...")
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
        print("SCREEN UPDATE SENT!")
        
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
        try:
            screenshot = pyautogui.screenshot().resize((800, 600))
            buffer = io.BytesIO()
            screenshot.save(buffer, format='JPEG', quality=70)
            img_data = base64.b64encode(buffer.getvalue()).decode()
            sio.emit('screen_update', {'image': img_data})
            print("MANUAL SCREENSHOT SENT")
        except Exception as e:
            print(f"MANUAL SCREENSHOT ERROR: {e}")

@sio.event
def screenshot_request():
    print("SCREENSHOT REQUEST EVENT RECEIVED")
    try:
        screenshot = pyautogui.screenshot().resize((800, 600))
        buffer = io.BytesIO()
        screenshot.save(buffer, format='JPEG', quality=70)
        img_data = base64.b64encode(buffer.getvalue()).decode()
        sio.emit('screen_update', {'image': img_data})
        print("SCREENSHOT REQUEST FULFILLED")
    except Exception as e:
        print(f"SCREENSHOT REQUEST ERROR: {e}")

@sio.event
def web_client_connected():
    print("\n=== WEB CLIENT CONNECTED EVENT ===")
    print("Client reloaded, sending fresh screenshot...")
    
    try:
        screenshot = pyautogui.screenshot().resize((800, 600))
        buffer = io.BytesIO()
        screenshot.save(buffer, format='JPEG', quality=70)
        img_data = base64.b64encode(buffer.getvalue()).decode()
        
        print(f"Reload screenshot data length: {len(img_data)}")
        sio.emit('screen_update', {'image': img_data})
        print("RELOAD SCREENSHOT SENT!")
        
        # 追加で2回送信
        for i in range(2):
            time.sleep(0.5)
            sio.emit('screen_update', {'image': img_data})
            print(f"ADDITIONAL RELOAD SCREENSHOT {i+1} SENT")
        
    except Exception as e:
        print(f"RELOAD SCREENSHOT ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    print("=== RELOAD RESPONSE COMPLETE ===")

# その他のイベントもキャッチ
@sio.on('*')
def catch_all(event, data):
    print(f"UNKNOWN EVENT: {event}, DATA: {data}")

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