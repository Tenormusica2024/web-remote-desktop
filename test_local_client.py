#!/usr/bin/env python3
"""
Test Local Client - ローカルテスト用 (スクリーン表示テスト)
"""
import socketio
import pyautogui
import base64
import io
import time
import sys

pyautogui.FAILSAFE = True

print("TEST LOCAL CLIENT - SCREEN DISPLAY TEST")
print(f"Python version: {sys.version}")

sio = socketio.Client(logger=True, engineio_logger=True)
# Connect to local test server
server_url = 'http://localhost:5000'

@sio.event
def connect():
    print("\n=== CONNECTION TO LOCAL SERVER ESTABLISHED ===")
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
        print("INITIAL SCREEN UPDATE SENT TO LOCAL SERVER!")
        
    except Exception as e:
        print(f"SCREENSHOT ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    print("=== LOCAL TEST CLIENT READY ===")

@sio.event
def disconnect():
    print("DISCONNECTED FROM LOCAL SERVER")

@sio.event
def connect_error(data):
    print(f"CONNECTION ERROR: {data}")

@sio.event  
def web_client_connected():
    print("\n=== WEB CLIENT CONNECTED TO LOCAL SERVER ===")
    print("Browser connected, sending fresh screenshot...")
    
    try:
        # Send screenshot immediately
        if send_screenshot():
            print("FRESH SCREENSHOT SENT TO LOCAL SERVER!")
        
        # Send additional screenshots for testing
        for i in range(2):
            time.sleep(0.5)
            if send_screenshot():
                print(f"ADDITIONAL SCREENSHOT {i+1} SENT")
        
    except Exception as e:
        print(f"LOCAL WEB CLIENT CONNECT ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    print("=== LOCAL WEB CLIENT CONNECT RESPONSE COMPLETE ===")

def send_screenshot():
    """Send screenshot to local server"""
    try:
        screenshot = pyautogui.screenshot().resize((800, 600))
        buffer = io.BytesIO()
        screenshot.save(buffer, format='JPEG', quality=70)
        img_data = base64.b64encode(buffer.getvalue()).decode()
        sio.emit('screen_update', {'image': img_data})
        print("SCREENSHOT SENT TO LOCAL SERVER")
        return True
    except Exception as e:
        print(f"SCREENSHOT ERROR: {e}")
        return False

@sio.event
def screenshot_request():
    print("SCREENSHOT REQUEST FROM LOCAL SERVER")
    send_screenshot()

# Catch all events
@sio.on('*')
def catch_all(event, *args):
    print(f"LOCAL SERVER EVENT: {event}, ARGS: {args}")

print(f"CONNECTING TO LOCAL TEST SERVER: {server_url}")

try:
    print("Attempting connection to local server...")
    sio.connect(server_url, transports=['polling'], wait_timeout=10)
    print("LOCAL CONNECTION SUCCESS!")
    print("Waiting for events from local server...")
    sio.wait()
    
except KeyboardInterrupt:
    print("\nSTOPPED BY USER")
    sio.disconnect()
except Exception as e:
    print(f"LOCAL CONNECTION FAILED: {e}")
    import traceback
    traceback.print_exc()
    input("Press Enter to exit...")