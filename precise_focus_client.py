#!/usr/bin/env python3
"""
Precise Focus Client - Accurate chat input targeting
"""
import socketio
import pyautogui
import base64
import io
import time

pyautogui.FAILSAFE = True

print("PRECISE FOCUS CLIENT STARTING...")

sio = socketio.Client()
server_url = 'https://remote-desktop-ycqe3vmjva-uc.a.run.app'

def get_chat_focus_position():
    """Get precise chat input position for Claude Code"""
    screen_width, screen_height = pyautogui.size()
    
    # Multiple possible chat input positions to try
    positions = [
        # Bottom-right area - different Y positions
        (int(screen_width * 0.75), int(screen_height * 0.95)),  # Very bottom
        (int(screen_width * 0.75), int(screen_height * 0.93)),  # Slightly higher
        (int(screen_width * 0.75), int(screen_height * 0.91)),  # Higher still
        (int(screen_width * 0.75), int(screen_height * 0.89)),  # Even higher
        (int(screen_width * 0.75), int(screen_height * 0.87)),  # More up
        
        # Slightly different X positions too
        (int(screen_width * 0.73), int(screen_height * 0.93)),  # Left + high
        (int(screen_width * 0.77), int(screen_height * 0.93)),  # Right + high
        (int(screen_width * 0.70), int(screen_height * 0.90)),  # More left
        (int(screen_width * 0.80), int(screen_height * 0.90)),  # More right
    ]
    
    return positions

def precise_chat_focus():
    """Precisely focus on Claude Code chat input"""
    positions = get_chat_focus_position()
    
    print("ATTEMPTING PRECISE FOCUS...")
    
    # Try each position
    for i, (x, y) in enumerate(positions):
        print(f"FOCUS ATTEMPT {i+1}: Clicking ({x}, {y})")
        pyautogui.click(x, y)
        time.sleep(0.1)
        
        # Try to focus text input
        try:
            # Move cursor to end of input
            pyautogui.press('end')
            time.sleep(0.05)
            # Small test - type space and delete to verify focus
            pyautogui.press('space')
            time.sleep(0.05)
            pyautogui.press('backspace')
            time.sleep(0.05)
        except:
            pass
    
    print("FOCUS SEQUENCE COMPLETE")

@sio.event
def connect():
    print("CONNECTED!")
    sio.emit('register_local_client')
    
    # Send screenshot
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
    print(f"COMMAND: {cmd}")
    
    if cmd == 'type':
        text = cmd_data.get('text', '')
        if text:
            print(f"TYPING: {text}")
            
            # Precise focus sequence
            precise_chat_focus()
            time.sleep(0.3)
            
            # Clear any existing text
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.1)
            
            # Type text character by character for reliability
            for char in text:
                pyautogui.press(char)
                time.sleep(0.02)
            
            print(f"TEXT TYPED: {text}")
            sio.emit('command_result', {'command': 'TYPE', 'success': True})
    
    elif cmd == 'key':
        key = cmd_data.get('key', '')
        if key:
            print(f"KEY PRESS: {key}")
            
            # Focus before key press (especially Enter)
            if key.lower() == 'enter':
                precise_chat_focus()
                time.sleep(0.2)
            
            pyautogui.press(key)
            print(f"KEY PRESSED: {key}")
            sio.emit('command_result', {'command': 'KEY', 'success': True})
    
    elif cmd == 'claude_focus_position':
        position = cmd_data.get('position', 'bottom-right')
        print(f"FOCUSING: {position}")
        
        if position == 'bottom-right':
            precise_chat_focus()
        else:
            # Standard positions for other corners
            w, h = pyautogui.size()
            coords = {
                'top-left': (int(w*0.25), int(h*0.25)),
                'top-right': (int(w*0.75), int(h*0.25)),
                'bottom-left': (int(w*0.25), int(h*0.75)),
                'center': (int(w*0.5), int(h*0.5))
            }
            
            if position in coords:
                x, y = coords[position]
                pyautogui.click(x, y)
        
        sio.emit('command_result', {'command': f'FOCUS_{position.upper()}', 'success': True})
    
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

@sio.event
def web_client_connected():
    print("WEB CLIENT CONNECTED")
    screenshot = pyautogui.screenshot().resize((800, 600))
    buffer = io.BytesIO()
    screenshot.save(buffer, format='JPEG', quality=70)
    img_data = base64.b64encode(buffer.getvalue()).decode()
    sio.emit('screen_update', {'image': img_data})

print("CONNECTING...")
sio.connect(server_url, transports=['polling'], wait_timeout=5)
print("CONNECTED! PRECISE FOCUS CLIENT OPERATIONAL")
sio.wait()