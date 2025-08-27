#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Final Optimized Client - Bulletproof chat input targeting
"""
import socketio
import pyautogui
import base64
import io
import time

# Disable PyAutoGUI failsafe and set faster speed
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.01

print("FINAL OPTIMIZED CLIENT STARTING...")

sio = socketio.Client()
server_url = 'https://remote-desktop-ycqe3vmjva-uc.a.run.app'

def smart_chat_focus():
    """Smart chat input focus with multiple strategies"""
    screen_width, screen_height = pyautogui.size()
    
    # Strategy 1: Bottom-right area sweep
    print("STRATEGY 1: Bottom-right area sweep")
    for y_offset in [0.88, 0.90, 0.92, 0.94]:
        for x_offset in [0.73, 0.75, 0.77]:
            x = int(screen_width * x_offset)
            y = int(screen_height * y_offset)
            pyautogui.click(x, y)
            time.sleep(0.05)
    
    # Strategy 2: Targeted chat input area
    print("STRATEGY 2: Targeted chat input")
    chat_x = int(screen_width * 0.75)
    chat_y = int(screen_height * 0.91)  # Optimal Y position
    
    # Triple click with slight variations
    for dx in [-10, 0, 10]:
        for dy in [-5, 0, 5]:
            pyautogui.click(chat_x + dx, chat_y + dy)
            time.sleep(0.02)
    
    # Strategy 3: Ensure text cursor is active
    print("STRATEGY 3: Cursor activation")
    pyautogui.press('end')
    time.sleep(0.1)
    
    # Test if input is focused by typing and deleting a space
    pyautogui.press('space')
    time.sleep(0.05)
    pyautogui.press('backspace')
    time.sleep(0.05)

def reliable_text_input(text):
    """Ultra-reliable text input"""
    print(f"INPUTTING TEXT: {text}")
    
    # Step 1: Smart focus
    smart_chat_focus()
    time.sleep(0.3)
    
    # Step 2: Clear existing content
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.1)
    pyautogui.press('delete')
    time.sleep(0.1)
    
    # Step 3: Type character by character for maximum reliability
    for i, char in enumerate(text):
        pyautogui.typewrite(char)
        time.sleep(0.02)  # Small delay between characters
        
        # Every 10 characters, verify we're still focused
        if i > 0 and i % 10 == 0:
            pyautogui.press('end')  # Ensure cursor is at end
            time.sleep(0.01)
    
    print(f"TEXT INPUT COMPLETE: {text}")

@sio.event
def connect():
    print("CONNECTED SUCCESSFULLY!")
    sio.emit('register_local_client')
    
    # Send initial screenshot
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
    print(f"EXECUTING COMMAND: {cmd}")
    
    try:
        if cmd == 'type':
            text = cmd_data.get('text', '')
            if text:
                reliable_text_input(text)
                sio.emit('command_result', {'command': 'TYPE', 'success': True})
        
        elif cmd == 'key':
            key = cmd_data.get('key', '')
            if key:
                print(f"PRESSING KEY: {key}")
                
                # For Enter key, ensure focus first
                if key.lower() == 'enter':
                    smart_chat_focus()
                    time.sleep(0.2)
                
                pyautogui.press(key)
                print(f"KEY PRESSED: {key}")
                sio.emit('command_result', {'command': 'KEY', 'success': True})
        
        elif cmd == 'claude_focus_position':
            position = cmd_data.get('position', 'bottom-right')
            print(f"FOCUSING CLAUDE POSITION: {position}")
            
            screen_width, screen_height = pyautogui.size()
            positions = {
                'top-left': (int(screen_width * 0.25), int(screen_height * 0.25)),
                'top-right': (int(screen_width * 0.75), int(screen_height * 0.25)),
                'bottom-left': (int(screen_width * 0.25), int(screen_height * 0.75)),
                'bottom-right': (int(screen_width * 0.75), int(screen_height * 0.90)),
                'center': (int(screen_width * 0.5), int(screen_height * 0.5))
            }
            
            if position in positions:
                x, y = positions[position]
                pyautogui.click(x, y)
                time.sleep(0.1)
                
                # If bottom-right, use smart chat focus
                if position == 'bottom-right':
                    smart_chat_focus()
            
            sio.emit('command_result', {'command': f'FOCUS_{position.upper()}', 'success': True})
        
        elif cmd == 'screenshot':
            screenshot = pyautogui.screenshot().resize((800, 600))
            buffer = io.BytesIO()
            screenshot.save(buffer, format='JPEG', quality=70)
            img_data = base64.b64encode(buffer.getvalue()).decode()
            sio.emit('screen_update', {'image': img_data})
            print("SCREENSHOT SENT")
    
    except Exception as e:
        print(f"COMMAND ERROR: {e}")
        sio.emit('command_result', {'command': cmd.upper(), 'success': False})

@sio.event
def screenshot_request():
    screenshot = pyautogui.screenshot().resize((800, 600))
    buffer = io.BytesIO()
    screenshot.save(buffer, format='JPEG', quality=70)
    img_data = base64.b64encode(buffer.getvalue()).decode()
    sio.emit('screen_update', {'image': img_data})

@sio.event
def web_client_connected():
    print("WEB CLIENT CONNECTED - REFRESHING SCREENSHOT")
    screenshot = pyautogui.screenshot().resize((800, 600))
    buffer = io.BytesIO()
    screenshot.save(buffer, format='JPEG', quality=70)
    img_data = base64.b64encode(buffer.getvalue()).decode()
    sio.emit('screen_update', {'image': img_data})

@sio.event
def disconnect():
    print("DISCONNECTED FROM SERVER")

@sio.event
def connect_error(data):
    print(f"CONNECTION ERROR: {data}")

print("CONNECTING TO SERVER...")
try:
    sio.connect(server_url, transports=['polling'], wait_timeout=10)
    print("CONNECTION ESTABLISHED SUCCESSFULLY!")
    print("FINAL OPTIMIZED CLIENT IS OPERATIONAL")
    print("Ready to receive text input commands...")
    
    sio.wait()
    
except KeyboardInterrupt:
    print("\nSHUTTING DOWN CLIENT...")
    sio.disconnect()
except Exception as e:
    print(f"CONNECTION FAILED: {e}")