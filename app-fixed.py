#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web Remote Desktop - Chrome Remote Desktop Alternative
Fixed version with correct template loading
"""

import os
import sys
import json
import time
import base64
import subprocess
from flask import Flask, render_template, request, jsonify, Response
from flask_socketio import SocketIO, emit
import pyautogui
from PIL import Image
import io
import threading
import webbrowser
from datetime import datetime

# Security settings
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ClaudeRemoteDesktop2024!'
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable template caching
socketio = SocketIO(app, cors_allowed_origins="*")

# Global state
clients = []
screenshot_thread = None
is_streaming = False

class RemoteDesktop:
    def __init__(self):
        self.screen_width, self.screen_height = pyautogui.size()
        self.quality = 80
        self.scale = 0.8
        
    def take_screenshot(self):
        try:
            screenshot = pyautogui.screenshot()
            new_width = int(self.screen_width * self.scale)
            new_height = int(self.screen_height * self.scale)
            screenshot = screenshot.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            buffer = io.BytesIO()
            screenshot.save(buffer, format='JPEG', quality=self.quality, optimize=True)
            img_str = base64.b64encode(buffer.getvalue()).decode()
            return f"data:image/jpeg;base64,{img_str}"
        except Exception as e:
            print(f"Screenshot error: {e}")
            return None
    
    def click(self, x, y):
        try:
            actual_x = int(x / self.scale)
            actual_y = int(y / self.scale)
            pyautogui.click(actual_x, actual_y)
            return True
        except Exception as e:
            print(f"Click error: {e}")
            return False
    
    def type_text(self, text):
        try:
            pyautogui.write(text, interval=0.01)
            return True
        except Exception as e:
            print(f"Type error: {e}")
            return False
    
    def key_press(self, key):
        try:
            pyautogui.press(key)
            return True
        except Exception as e:
            print(f"Key press error: {e}")
            return False
    
    def scroll(self, x, y, direction):
        try:
            actual_x = int(x / self.scale)
            actual_y = int(y / self.scale)
            pyautogui.scroll(direction, x=actual_x, y=actual_y)
            return True
        except Exception as e:
            print(f"Scroll error: {e}")
            return False

remote_desktop = RemoteDesktop()

def screenshot_streaming():
    global is_streaming
    while is_streaming:
        try:
            screenshot_data = remote_desktop.take_screenshot()
            if screenshot_data and clients:
                socketio.emit('screenshot', {'image': screenshot_data})
            time.sleep(1/15)
        except Exception as e:
            print(f"Streaming error: {e}")
            time.sleep(1)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'screen_size': f"{remote_desktop.screen_width}x{remote_desktop.screen_height}",
        'clients': len(clients),
        'streaming': is_streaming,
        'timestamp': datetime.now().isoformat()
    })

@socketio.on('connect')
def handle_connect():
    global screenshot_thread, is_streaming
    
    clients.append(request.sid)
    print(f"Client connected: {request.sid} (Total: {len(clients)})")
    
    if len(clients) == 1 and not is_streaming:
        is_streaming = True
        screenshot_thread = threading.Thread(target=screenshot_streaming)
        screenshot_thread.daemon = True
        screenshot_thread.start()
        print("Screenshot streaming started")
    
    emit('connected', {
        'screen_width': int(remote_desktop.screen_width * remote_desktop.scale),
        'screen_height': int(remote_desktop.screen_height * remote_desktop.scale)
    })

@socketio.on('disconnect')
def handle_disconnect():
    global is_streaming
    
    if request.sid in clients:
        clients.remove(request.sid)
        print(f"Client disconnected: {request.sid} (Remaining: {len(clients)})")
    
    if len(clients) == 0:
        is_streaming = False
        print("Screenshot streaming stopped")

@socketio.on('click')
def handle_click(data):
    x = data.get('x', 0)
    y = data.get('y', 0)
    success = remote_desktop.click(x, y)
    emit('action_result', {'action': 'click', 'success': success, 'x': x, 'y': y})
    print(f"Click: ({x}, {y}) - {'Success' if success else 'Failed'}")

@socketio.on('type')
def handle_type(data):
    text = data.get('text', '')
    success = remote_desktop.type_text(text)
    emit('action_result', {'action': 'type', 'success': success, 'length': len(text)})
    print(f"Type: '{text[:50]}...' - {'Success' if success else 'Failed'}")

@socketio.on('key')
def handle_key(data):
    key = data.get('key', '')
    success = remote_desktop.key_press(key)
    emit('action_result', {'action': 'key', 'success': success, 'key': key})
    print(f"Key: '{key}' - {'Success' if success else 'Failed'}")

@socketio.on('scroll')
def handle_scroll(data):
    x = data.get('x', 0)
    y = data.get('y', 0)
    direction = data.get('direction', 0)
    success = remote_desktop.scroll(x, y, direction)
    emit('action_result', {'action': 'scroll', 'success': success})
    print(f"Scroll: ({x}, {y}) direction {direction} - {'Success' if success else 'Failed'}")

if __name__ == '__main__':
    print("=" * 60)
    print("Chrome Remote Desktop Alternative - Web Version")
    print("=" * 60)
    print()
    print("Server starting...")
    port = 8085  # Port change to avoid conflicts
    print(f"Access URL: http://localhost:{port}")
    print(f"LAN Access: http://192.168.3.3:{port}")
    print()
    print("Features:")
    print("- No admin privileges required")
    print("- No Docker required") 
    print("- Local network only")
    print("- Chrome Remote Desktop alternative")
    print("- Remote Mode for same-PC operation fix")
    print()
    print("=" * 60)
    
    def open_browser():
        time.sleep(5)
        webbrowser.open(f'http://localhost:{port}')
    
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    try:
        socketio.run(app, host='0.0.0.0', port=port, debug=False)
    except KeyboardInterrupt:
        print("\\nStopping server...")
    except Exception as e:
        print(f"Server error: {e}")
    finally:
        is_streaming = False
        print("Server stopped")