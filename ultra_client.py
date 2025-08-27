#!/usr/bin/env python3
"""
Ultra Fast Remote Desktop Client
Instant connection and immediate response
"""
import socketio
import pyautogui
import base64
import io
import time

# Ultra-fast settings
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.01

print("ULTRA CLIENT STARTING...")

# Simple, immediate connection
sio = socketio.Client(logger=False, engineio_logger=False)
server_url = 'https://remote-desktop-ycqe3vmjva-uc.a.run.app'

def send_screenshot_now():
    """Send screenshot immediately"""
    try:
        screenshot = pyautogui.screenshot().resize((800, 600))
        buffer = io.BytesIO()
        screenshot.save(buffer, format='JPEG', quality=65)
        img_data = base64.b64encode(buffer.getvalue()).decode()
        sio.emit('screen_update', {'image': img_data})
        print("SCREENSHOT SENT")
    except Exception as e:
        print(f"SCREENSHOT ERROR: {e}")

@sio.event
def connect():
    print("CONNECTED INSTANTLY!")
    sio.emit('register_local_client')
    # Send screenshot 3 times for reliability
    for i in range(3):
        send_screenshot_now()
        time.sleep(0.1)
    print("CLIENT READY - CONNECTION ESTABLISHED")

@sio.event
def disconnect():
    print("DISCONNECTED")

@sio.event
def execute_command(data):
    cmd = data.get('command')
    cmd_data = data.get('data', {})
    print(f"EXECUTING: {cmd}")
    
    if cmd == 'type':
        text = cmd_data.get('text', '')
        if text:
            print(f"TYPING: {text}")
            # Ultra-reliable text input
            w, h = pyautogui.size()
            
            # Multiple focus attempts
            positions = [
                (int(w*0.75), int(h*0.90)),
                (int(w*0.75), int(h*0.88)),
                (int(w*0.73), int(h*0.92))
            ]
            
            for x, y in positions:
                pyautogui.click(x, y)
                time.sleep(0.05)
            
            # Clear and type
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.1)
            pyautogui.typewrite(text, interval=0.04)
            
            print(f"TEXT SENT: {text}")
            sio.emit('command_result', {'command': 'TYPE', 'success': True})
    
    elif cmd == 'key':
        key = cmd_data.get('key', '')
        if key:
            print(f"KEY: {key}")
            if key.lower() == 'enter':
                # Focus before Enter
                w, h = pyautogui.size()
                pyautogui.click(int(w*0.75), int(h*0.90))
                time.sleep(0.1)
            
            pyautogui.press(key)
            print(f"KEY PRESSED: {key}")
            sio.emit('command_result', {'command': 'KEY', 'success': True})
    
    elif cmd == 'claude_focus_position':
        position = cmd_data.get('position', 'bottom-right')
        w, h = pyautogui.size()
        
        coords = {
            'top-left': (int(w*0.25), int(h*0.25)),
            'top-right': (int(w*0.75), int(h*0.25)),
            'bottom-left': (int(w*0.25), int(h*0.75)),
            'bottom-right': (int(w*0.75), int(h*0.90)),
            'center': (int(w*0.5), int(h*0.5))
        }
        
        if position in coords:
            x, y = coords[position]
            pyautogui.click(x, y)
            print(f"FOCUSED: {position} at ({x}, {y})")
            sio.emit('command_result', {'command': f'FOCUS_{position.upper()}', 'success': True})
    
    elif cmd == 'screenshot':
        send_screenshot_now()

@sio.event
def screenshot_request():
    print("SCREENSHOT REQUESTED")
    send_screenshot_now()

@sio.event
def web_client_connected():
    print("WEB CLIENT CONNECTED - SENDING FRESH SCREENSHOT")
    # Send multiple screenshots for immediate display
    for i in range(2):
        send_screenshot_now()
        time.sleep(0.2)

@sio.event
def connect_error(data):
    print(f"CONNECTION ERROR: {data}")

print(f"CONNECTING TO: {server_url}")

try:
    # Ultra-fast connection
    sio.connect(server_url, transports=['polling'], wait_timeout=3)
    print("CONNECTION SUCCESS!")
    
    # Keep connection alive
    sio.wait()
    
except Exception as e:
    print(f"CONNECTION FAILED: {e}")
    print("RETRYING...")
    
    # Retry once
    try:
        sio.connect(server_url, transports=['polling'], wait_timeout=5)
        print("RETRY SUCCESS!")
        sio.wait()
    except Exception as retry_error:
        print(f"RETRY FAILED: {retry_error}")
        input("Press Enter to exit...")