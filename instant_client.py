#!/usr/bin/env python3
"""
Instant Connect Client - No delays, immediate response
"""
import socketio
import pyautogui
import base64
import io
import time

pyautogui.FAILSAFE = True

sio = socketio.Client()
server_url = 'https://remote-desktop-ycqe3vmjva-uc.a.run.app'

@sio.event
def connect():
    print('CONNECTED!')
    sio.emit('register_local_client')
    # Send screenshot immediately
    screenshot = pyautogui.screenshot().resize((800, 600))
    buffer = io.BytesIO()
    screenshot.save(buffer, format='JPEG', quality=70)
    img_data = base64.b64encode(buffer.getvalue()).decode()
    sio.emit('screen_update', {'image': img_data})
    print('SCREENSHOT SENT - READY!')

@sio.event
def execute_command(data):
    cmd = data.get('command')
    cmd_data = data.get('data', {})
    
    if cmd == 'type':
        text = cmd_data.get('text', '')
        if text:
            # Focus Claude bottom-right
            w, h = pyautogui.size()
            pyautogui.click(int(w*0.75), int(h*0.90))
            time.sleep(0.1)
            pyautogui.typewrite(text)
            print(f'TYPED: {text}')
            sio.emit('command_result', {'command': 'TYPE', 'success': True})
    
    elif cmd == 'key':
        key = cmd_data.get('key', '')
        if key == 'enter':
            w, h = pyautogui.size()
            pyautogui.click(int(w*0.75), int(h*0.90))
            time.sleep(0.1)
        pyautogui.press(key)
        print(f'KEY: {key}')
        sio.emit('command_result', {'command': 'KEY', 'success': True})
    
    elif cmd == 'screenshot':
        screenshot = pyautogui.screenshot().resize((800, 600))
        buffer = io.BytesIO()
        screenshot.save(buffer, format='JPEG', quality=70)
        img_data = base64.b64encode(buffer.getvalue()).decode()
        sio.emit('screen_update', {'image': img_data})

@sio.event
def screenshot_request():
    screenshot = pyautogui.screenshot().resize((800, 600))
    buffer = io.BytesIO()
    screenshot.save(buffer, format='JPEG', quality=70)
    img_data = base64.b64encode(buffer.getvalue()).decode()
    sio.emit('screen_update', {'image': img_data})

@sio.event
def web_client_connected():
    print('WEB CLIENT CONNECTED - SENDING SCREENSHOT')
    screenshot = pyautogui.screenshot().resize((800, 600))
    buffer = io.BytesIO()
    screenshot.save(buffer, format='JPEG', quality=70)
    img_data = base64.b64encode(buffer.getvalue()).decode()
    sio.emit('screen_update', {'image': img_data})

print("INSTANT CLIENT STARTING...")
sio.connect(server_url, transports=['polling'])
print("CONNECTED! Ready for commands.")
sio.wait()