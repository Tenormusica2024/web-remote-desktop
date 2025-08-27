#!/usr/bin/env python3
"""
Simple Working Client - Based on successful connection test
"""
import socketio
import pyautogui
import base64
import io
import time

pyautogui.FAILSAFE = True

print("SIMPLE WORKING CLIENT STARTING...")

sio = socketio.Client()
server_url = 'https://remote-desktop-ycqe3vmjva-uc.a.run.app'

@sio.event
def connect():
    print("CONNECTED!")
    sio.emit('register_local_client')
    
    # Send screenshot after 1 second
    time.sleep(1)
    screenshot = pyautogui.screenshot().resize((800, 600))
    buffer = io.BytesIO()
    screenshot.save(buffer, format='JPEG', quality=70)
    img_data = base64.b64encode(buffer.getvalue()).decode()
    sio.emit('screen_update', {'image': img_data})
    print("SCREENSHOT SENT - CLIENT READY!")

@sio.event
def execute_command(data):
    cmd = data.get('command')
    cmd_data = data.get('data', {})
    print(f"COMMAND: {cmd} - {cmd_data}")
    
    if cmd == 'type':
        text = cmd_data.get('text', '')
        if text:
            # Simple focus and type
            w, h = pyautogui.size()
            pyautogui.click(int(w*0.75), int(h*0.90))  # Bottom-right
            time.sleep(0.2)
            
            # Clear existing text and type new
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.1)
            pyautogui.typewrite(text, interval=0.05)
            
            print(f"TYPED: {text}")
            sio.emit('command_result', {'command': 'TYPE', 'success': True})
    
    elif cmd == 'key':
        key = cmd_data.get('key', '')
        if key:
            # Focus before key press
            if key.lower() == 'enter':
                w, h = pyautogui.size()
                pyautogui.click(int(w*0.75), int(h*0.90))
                time.sleep(0.2)
            
            pyautogui.press(key)
            print(f"KEY: {key}")
            sio.emit('command_result', {'command': 'KEY', 'success': True})
    
    elif cmd == 'screenshot':
        screenshot = pyautogui.screenshot().resize((800, 600))
        buffer = io.BytesIO()
        screenshot.save(buffer, format='JPEG', quality=70)
        img_data = base64.b64encode(buffer.getvalue()).decode()
        sio.emit('screen_update', {'image': img_data})
        print("SCREENSHOT SENT")

@sio.event
def screenshot_request():
    screenshot = pyautogui.screenshot().resize((800, 600))
    buffer = io.BytesIO()
    screenshot.save(buffer, format='JPEG', quality=70)
    img_data = base64.b64encode(buffer.getvalue()).decode()
    sio.emit('screen_update', {'image': img_data})
    print("SCREENSHOT REQUESTED AND SENT")

@sio.event
def web_client_connected():
    print("WEB CLIENT CONNECTED - SENDING SCREENSHOT")
    screenshot = pyautogui.screenshot().resize((800, 600))
    buffer = io.BytesIO()
    screenshot.save(buffer, format='JPEG', quality=70)
    img_data = base64.b64encode(buffer.getvalue()).decode()
    sio.emit('screen_update', {'image': img_data})

print("CONNECTING...")
sio.connect(server_url, transports=['polling'], wait_timeout=5)
print("SUCCESS! CLIENT OPERATIONAL")
sio.wait()