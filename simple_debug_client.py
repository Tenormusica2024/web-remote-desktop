#!/usr/bin/env python3
"""
Simple Debug Client - ASCII only
"""
import socketio
import pyautogui
import base64
import io
import time

pyautogui.FAILSAFE = True

print("SIMPLE DEBUG CLIENT STARTING")

sio = socketio.Client()
server_url = 'https://remote-desktop-ycqe3vmjva-uc.a.run.app'

@sio.event
def connect():
    print("CONNECTED!")
    print("Registering as local client...")
    sio.emit('register_local_client')
    print("PC client registered")
    
    print("Taking screenshot...")
    screenshot = pyautogui.screenshot().resize((800, 600))
    buffer = io.BytesIO()
    screenshot.save(buffer, format='JPEG', quality=70)
    img_data = base64.b64encode(buffer.getvalue()).decode()
    
    print("Sending screenshot...")
    sio.emit('screen_update', {'image': img_data})
    print("SCREENSHOT SENT - CLIENT READY!")
    print("=== PC CLIENT IS READY ===")

@sio.event
def disconnect():
    print("DISCONNECTED")

@sio.event
def connect_error(data):
    print(f"CONNECTION ERROR: {data}")

@sio.event
def execute_command(data):
    cmd = data.get('command')
    cmd_data = data.get('data', {})
    print(f"COMMAND RECEIVED: {cmd}")
    
    if cmd == 'type':
        text = cmd_data.get('text', '')
        if text:
            print(f"TYPING TEXT: {text}")
            w, h = pyautogui.size()
            click_x = int(w*0.75)
            click_y = int(h*0.90)
            print(f"CLICKING: ({click_x}, {click_y})")
            pyautogui.click(click_x, click_y)
            time.sleep(0.1)
            pyautogui.typewrite(text)
            print(f"TEXT TYPED: {text}")
            sio.emit('command_result', {'command': 'TYPE', 'success': True})
    
    elif cmd == 'key':
        key = cmd_data.get('key', '')
        if key:
            print(f"PRESSING KEY: {key}")
            if key == 'enter':
                w, h = pyautogui.size()
                pyautogui.click(int(w*0.75), int(h*0.90))
                time.sleep(0.1)
            pyautogui.press(key)
            print(f"KEY PRESSED: {key}")
            sio.emit('command_result', {'command': 'KEY', 'success': True})
    
    elif cmd == 'screenshot':
        print("SCREENSHOT REQUEST")
        screenshot = pyautogui.screenshot().resize((800, 600))
        buffer = io.BytesIO()
        screenshot.save(buffer, format='JPEG', quality=70)
        img_data = base64.b64encode(buffer.getvalue()).decode()
        sio.emit('screen_update', {'image': img_data})
        print("SCREENSHOT SENT")

@sio.event
def screenshot_request():
    print("SCREENSHOT REQUEST RECEIVED")
    screenshot = pyautogui.screenshot().resize((800, 600))
    buffer = io.BytesIO()
    screenshot.save(buffer, format='JPEG', quality=70)
    img_data = base64.b64encode(buffer.getvalue()).decode()
    sio.emit('screen_update', {'image': img_data})
    print("SCREENSHOT RESPONSE SENT")

@sio.event
def web_client_connected():
    print("WEB CLIENT CONNECTED!")
    print("Sending reload screenshot...")
    screenshot = pyautogui.screenshot().resize((800, 600))
    buffer = io.BytesIO()
    screenshot.save(buffer, format='JPEG', quality=70)
    img_data = base64.b64encode(buffer.getvalue()).decode()
    sio.emit('screen_update', {'image': img_data})
    print("RELOAD SCREENSHOT SENT")

print("CONNECTING TO SERVER...")
print(f"URL: {server_url}")

try:
    sio.connect(server_url, transports=['polling'], wait_timeout=10)
    print("CONNECTION ESTABLISHED!")
    print("WAITING FOR EVENTS...")
    sio.wait()
except KeyboardInterrupt:
    print("STOPPED BY USER")
    sio.disconnect()
except Exception as e:
    print(f"ERROR: {e}")
    input("Press Enter to exit...")