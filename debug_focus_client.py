#!/usr/bin/env python3
"""
Debug Focus Client - Visual debugging for chat focus
"""
import socketio
import pyautogui
import base64
import io
import time

pyautogui.FAILSAFE = True

print("DEBUG FOCUS CLIENT STARTING...")

sio = socketio.Client()
server_url = 'https://remote-desktop-ycqe3vmjva-uc.a.run.app'

def debug_screen_positions():
    """Debug screen positions visually"""
    screen_width, screen_height = pyautogui.size()
    print(f"SCREEN SIZE: {screen_width}x{screen_height}")
    
    # Calculate all possible chat positions
    positions = []
    for x_percent in [0.70, 0.73, 0.75, 0.77, 0.80]:
        for y_percent in [0.85, 0.87, 0.89, 0.91, 0.93, 0.95, 0.97]:
            x = int(screen_width * x_percent)
            y = int(screen_height * y_percent)
            positions.append((x, y, f"{x_percent*100:.0f}%,{y_percent*100:.0f}%"))
    
    return positions

def test_focus_position(x, y, label):
    """Test a specific focus position"""
    print(f"TESTING: {label} at ({x}, {y})")
    
    # Click the position
    pyautogui.click(x, y)
    time.sleep(0.2)
    
    # Test if it's a text input by trying to select all
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.1)
    
    # Try typing a test character
    pyautogui.typewrite('test', interval=0.05)
    time.sleep(0.1)
    
    # Clear the test text
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.1)
    pyautogui.press('delete')
    time.sleep(0.1)
    
    print(f"COMPLETED TEST: {label}")

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
            
            # Debug all positions
            positions = debug_screen_positions()
            print(f"TESTING {len(positions)} POSITIONS...")
            
            # Try the most likely positions first
            best_positions = [
                positions[i] for i in [10, 15, 20, 25, 30]  # Mid-range positions
            ]
            
            for x, y, label in best_positions:
                print(f"TRYING: {label}")
                pyautogui.click(x, y)
                time.sleep(0.1)
            
            # Focus on most likely position
            screen_width, screen_height = pyautogui.size()
            best_x = int(screen_width * 0.75)
            best_y = int(screen_height * 0.91)
            pyautogui.click(best_x, best_y)
            time.sleep(0.3)
            
            # Clear existing text
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.1)
            
            # Type the text
            pyautogui.typewrite(text, interval=0.03)
            
            print(f"TEXT TYPED: {text}")
            sio.emit('command_result', {'command': 'TYPE', 'success': True})
    
    elif cmd == 'key':
        key = cmd_data.get('key', '')
        if key:
            print(f"KEY PRESS: {key}")
            
            if key.lower() == 'enter':
                # Focus before Enter
                screen_width, screen_height = pyautogui.size()
                x = int(screen_width * 0.75)
                y = int(screen_height * 0.91)
                pyautogui.click(x, y)
                time.sleep(0.2)
            
            pyautogui.press(key)
            print(f"KEY PRESSED: {key}")
            sio.emit('command_result', {'command': 'KEY', 'success': True})
    
    elif cmd == 'debug_positions':
        print("RUNNING POSITION DEBUG...")
        positions = debug_screen_positions()
        
        # Test top 10 most likely positions
        for i, (x, y, label) in enumerate(positions[10:20]):
            test_focus_position(x, y, f"Test {i+1}: {label}")
            time.sleep(0.5)
        
        sio.emit('command_result', {'command': 'DEBUG', 'success': True})
    
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
print("CONNECTED! DEBUG FOCUS CLIENT OPERATIONAL")
sio.wait()