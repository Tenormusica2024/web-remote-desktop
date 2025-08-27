#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLEAN Remote Desktop Server - Port 8090 - GUARANTEED Remote Mode Button
Completely fresh implementation to avoid any caching issues
"""

import os
import sys
import json
import time
import base64
from flask import Flask, request, jsonify
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
app.config['SECRET_KEY'] = 'CleanRemoteDesktop2024!'
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
            # Enhanced Japanese input support
            if text:
                # Handle Japanese characters properly
                pyautogui.write(text, interval=0.05)  # Slower for better compatibility
                return True
            return False
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
    html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Remote Desktop - CLEAN VERSION</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        body { margin: 0; font-family: Arial, sans-serif; background: #111; color: white; }
        .header { background: #333; padding: 15px; display: flex; justify-content: space-between; align-items: center; }
        .title { font-size: 20px; color: #4CAF50; }
        .controls { display: flex; gap: 10px; }
        .btn { padding: 10px 15px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; }
        .btn-primary { background: #2196F3; color: white; }
        .btn-warning { background: #FF5722; color: white; animation: blink 1s infinite; }
        @keyframes blink { 0%, 50% { opacity: 1; } 51%, 100% { opacity: 0.5; } }
        .status { padding: 8px 12px; border-radius: 20px; font-size: 14px; }
        .connected { background: #4CAF50; }
        .disconnected { background: #F44336; }
        .container { height: calc(100vh - 80px); display: flex; justify-content: center; align-items: center; background: #000; }
        #screen { max-width: 100%; max-height: 100%; border: 3px solid #2196F3; }
        .loading { text-align: center; color: #888; }
        .toolbar { position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); background: rgba(0,0,0,0.8); padding: 10px; border-radius: 10px; display: flex; gap: 8px; flex-wrap: wrap; justify-content: center; }
        .toolbar input { padding: 8px; border: 1px solid #555; border-radius: 4px; background: #222; color: white; width: 280px; margin-bottom: 5px; }
        .btn-send { background: #4CAF50 !important; color: white !important; font-weight: bold !important; padding: 10px 16px !important; font-size: 14px !important; }
        .btn-send:hover { background: #45a049 !important; transform: scale(1.05); }
        .btn-enter { background: #2196F3 !important; color: white !important; font-weight: bold !important; padding: 10px 16px !important; font-size: 14px !important; }
        .btn-enter:hover { background: #1976D2 !important; transform: scale(1.05); }
        .feedback { position: fixed; top: 100px; left: 20px; padding: 15px; border-radius: 5px; max-width: 400px; opacity: 0; transition: opacity 0.3s; }
        .feedback.show { opacity: 1; }
        .feedback.success { background: #4CAF50; }
        .feedback.error { background: #F44336; }
    </style>
</head>
<body>
    <div class="header">
        <div class="title">🖥️ CLEAN Remote Desktop</div>
        <div class="controls">
            <div id="status" class="status disconnected">DISCONNECTED</div>
            <button id="remote-btn" class="btn btn-warning">⚠️ REMOTE MODE: OFF</button>
            <button id="fullscreen-btn" class="btn btn-primary">FULLSCREEN</button>
        </div>
    </div>
    
    <div class="container">
        <div class="loading" id="loading">
            <h2>Connecting to Remote Desktop...</h2>
            <p>Port 8090 - Clean Version</p>
        </div>
        <img id="screen" style="display: none;" alt="Remote Screen">
    </div>
    
    <div class="toolbar">
        <input type="text" id="textbox" placeholder="Type here and press Enter to send to remote PC">
        <button id="send-btn" class="btn btn-primary btn-send">📤 SEND TEXT</button>
        <button id="enter-btn" class="btn btn-primary btn-enter">⏎ ENTER</button>
        <button id="ctrl-c-btn" class="btn btn-primary">CTRL+C</button>
        <button id="ctrl-v-btn" class="btn btn-primary">CTRL+V</button>
    </div>
    
    <div id="feedback" class="feedback"></div>

    <script>
        const socket = io();
        let connected = false;
        let remoteMode = false;
        let screenW = 0, screenH = 0;
        
        const statusEl = document.getElementById('status');
        const loadingEl = document.getElementById('loading');
        const screenEl = document.getElementById('screen');
        const remoteBtnEl = document.getElementById('remote-btn');
        const textboxEl = document.getElementById('textbox');
        const feedbackEl = document.getElementById('feedback');
        
        function showMessage(msg, type = 'success') {
            feedbackEl.textContent = msg;
            feedbackEl.className = `feedback ${type} show`;
            setTimeout(() => feedbackEl.classList.remove('show'), 4000);
        }
        
        socket.on('connected', (data) => {
            connected = true;
            screenW = data.screen_width;
            screenH = data.screen_height;
            statusEl.textContent = 'CONNECTED';
            statusEl.className = 'status connected';
            loadingEl.style.display = 'none';
            screenEl.style.display = 'block';
            showMessage(`Connected! Screen: ${screenW}x${screenH}`, 'success');
            setTimeout(() => showMessage('⚠️ CRITICAL: Click REMOTE MODE button to turn ON!', 'error'), 2000);
        });
        
        socket.on('disconnect', () => {
            connected = false;
            statusEl.textContent = 'DISCONNECTED';
            statusEl.className = 'status disconnected';
            screenEl.style.display = 'none';
            loadingEl.style.display = 'block';
        });
        
        socket.on('screenshot', (data) => {
            if (data.image) screenEl.src = data.image;
        });
        
        socket.on('action_result', (data) => {
            showMessage(`${data.action}: ${data.success ? 'SUCCESS' : 'FAILED'}`, data.success ? 'success' : 'error');
        });
        
        // CRITICAL: REMOTE MODE BUTTON CLICK HANDLER
        remoteBtnEl.addEventListener('click', () => {
            // Remember the currently focused element
            const currentFocus = document.activeElement;
            
            remoteMode = !remoteMode;
            if (remoteMode) {
                remoteBtnEl.textContent = '✅ REMOTE MODE: ON';
                remoteBtnEl.className = 'btn btn-primary';
                showMessage('✅ REMOTE MODE ON: Safe to click screen!', 'success');
            } else {
                remoteBtnEl.textContent = '⚠️ REMOTE MODE: OFF';
                remoteBtnEl.className = 'btn btn-warning';
                showMessage('⚠️ REMOTE MODE OFF: Same-PC interference risk!', 'error');
            }
            
            // Restore focus to the previously focused element
            if (currentFocus && currentFocus !== remoteBtnEl && currentFocus.tagName !== 'BODY') {
                setTimeout(() => {
                    currentFocus.focus();
                }, 10);
            }
        });
        
        screenEl.addEventListener('click', (e) => {
            if (!connected) return;
            if (!remoteMode) {
                showMessage('⚠️ Turn ON Remote Mode first!', 'error');
                return;
            }
            
            e.preventDefault();
            const rect = screenEl.getBoundingClientRect();
            const x = Math.round((e.clientX - rect.left) * (screenW / rect.width));
            const y = Math.round((e.clientY - rect.top) * (screenH / rect.height));
            socket.emit('click', { x, y });
            showMessage(`Clicked: ${x},${y}`, 'success');
        });
        
        screenEl.addEventListener('wheel', (e) => {
            if (!connected) return;
            e.preventDefault();
            const rect = screenEl.getBoundingClientRect();
            const x = Math.round((e.clientX - rect.left) * (screenW / rect.width));
            const y = Math.round((e.clientY - rect.top) * (screenH / rect.height));
            const dir = e.deltaY > 0 ? -3 : 3;
            socket.emit('scroll', { x, y, direction: dir });
        });
        
        // Enhanced text sending function
        function sendTextToRemote() {
            const text = textboxEl.value.trim();
            if (!text) {
                showMessage('⚠️ Please enter text first!', 'error');
                return;
            }
            if (!connected) {
                showMessage('❌ Not connected to remote desktop!', 'error');
                return;
            }
            
            showMessage(`📤 Sending: "${text.substring(0, 20)}${text.length > 20 ? '...' : ''}"`, 'success');
            socket.emit('type', { text });
            textboxEl.value = '';
            
            // Extra feedback for mobile users
            if (navigator.userAgent.match(/Android|iPhone|iPad/i)) {
                textboxEl.placeholder = 'Text sent! Type next message...';
                setTimeout(() => {
                    textboxEl.placeholder = 'Type here and press Enter to send to remote PC';
                }, 2000);
            }
        }
        
        // Multiple event handlers for better mobile support
        textboxEl.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                sendTextToRemote();
            }
        });
        
        textboxEl.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                sendTextToRemote();
            }
        });
        
        document.getElementById('send-btn').addEventListener('click', (e) => {
            e.preventDefault();
            sendTextToRemote();
        });
        
        document.getElementById('send-btn').addEventListener('touchend', (e) => {
            e.preventDefault();
            sendTextToRemote();
        });
        
        // Enhanced Enter key function
        function sendEnterKey() {
            if (!connected) {
                showMessage('❌ Not connected to remote desktop!', 'error');
                return;
            }
            showMessage('⏎ Sending Enter key', 'success');
            socket.emit('key', { key: 'enter' });
        }
        
        document.getElementById('enter-btn').addEventListener('click', (e) => {
            e.preventDefault();
            sendEnterKey();
        });
        
        document.getElementById('enter-btn').addEventListener('touchend', (e) => {
            e.preventDefault();
            sendEnterKey();
        });
        
        document.getElementById('ctrl-c-btn').addEventListener('click', () => {
            if (connected) {
                showMessage('📋 Sending Ctrl+C', 'success');
                socket.emit('key', { key: 'ctrl+c' });
            }
        });
        
        document.getElementById('ctrl-v-btn').addEventListener('click', () => {
            if (connected) socket.emit('key', { key: 'ctrl+v' });
        });
        
        document.getElementById('fullscreen-btn').addEventListener('click', () => {
            if (document.fullscreenElement) {
                document.exitFullscreen();
            } else {
                document.documentElement.requestFullscreen();
            }
        });
        
        // Periodic reminder to turn on remote mode
        setInterval(() => {
            if (connected && !remoteMode) {
                showMessage('⚠️ REMINDER: Turn ON Remote Mode for safe operation!', 'error');
            }
        }, 20000);
        
        showMessage('Starting Clean Remote Desktop on Port 8090...', 'success');
    </script>
</body>
</html>"""
    return html

@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'version': 'clean',
        'port': 8090,
        'screen_size': f"{remote_desktop.screen_width}x{remote_desktop.screen_height}",
        'clients': len(clients),
        'streaming': is_streaming,
        'timestamp': datetime.now().isoformat()
    })

@socketio.on('connect')
def handle_connect():
    global screenshot_thread, is_streaming
    
    clients.append(request.sid)
    print(f"[CLEAN] Client connected: {request.sid} (Total: {len(clients)})")
    
    if len(clients) == 1 and not is_streaming:
        is_streaming = True
        screenshot_thread = threading.Thread(target=screenshot_streaming)
        screenshot_thread.daemon = True
        screenshot_thread.start()
        print("[CLEAN] Screenshot streaming started")
    
    emit('connected', {
        'screen_width': int(remote_desktop.screen_width * remote_desktop.scale),
        'screen_height': int(remote_desktop.screen_height * remote_desktop.scale)
    })

@socketio.on('disconnect')
def handle_disconnect():
    global is_streaming
    
    if request.sid in clients:
        clients.remove(request.sid)
        print(f"[CLEAN] Client disconnected: {request.sid} (Remaining: {len(clients)})")
    
    if len(clients) == 0:
        is_streaming = False
        print("[CLEAN] Screenshot streaming stopped")

@socketio.on('click')
def handle_click(data):
    x = data.get('x', 0)
    y = data.get('y', 0)
    success = remote_desktop.click(x, y)
    emit('action_result', {'action': 'CLICK', 'success': success, 'x': x, 'y': y})
    print(f"[CLEAN] Click: ({x}, {y}) - {'Success' if success else 'Failed'}")

@socketio.on('type')
def handle_type(data):
    text = data.get('text', '')
    success = remote_desktop.type_text(text)
    emit('action_result', {'action': 'TYPE', 'success': success, 'text': text[:20]})
    print(f"[CLEAN] Type: '{text[:30]}' - {'Success' if success else 'Failed'}")

@socketio.on('key')
def handle_key(data):
    key = data.get('key', '')
    success = remote_desktop.key_press(key)
    emit('action_result', {'action': 'KEY', 'success': success, 'key': key})
    print(f"[CLEAN] Key: '{key}' - {'Success' if success else 'Failed'}")

@socketio.on('scroll')
def handle_scroll(data):
    x = data.get('x', 0)
    y = data.get('y', 0)
    direction = data.get('direction', 0)
    success = remote_desktop.scroll(x, y, direction)
    emit('action_result', {'action': 'SCROLL', 'success': success})
    print(f"[CLEAN] Scroll: ({x}, {y}) dir={direction} - {'Success' if success else 'Failed'}")

if __name__ == '__main__':
    print("=" * 70)
    print("CLEAN REMOTE DESKTOP SERVER - PORT 8090")
    print("=" * 70)
    print()
    print("COMPLETELY NEW SERVER - NO CACHE ISSUES")
    print("GUARANTEED REMOTE MODE BUTTON DISPLAY")
    print()
    
    port = 8091  # NEW PORT TO AVOID ALL CACHING
    print(f"NEW ACCESS URL: http://localhost:{port}")
    print(f"LAN ACCESS: http://192.168.3.3:{port}")
    print()
    print("USAGE STEPS:")
    print("1. Access the NEW URL above")
    print("2. Look for 'REMOTE MODE: OFF' button (top-right)")
    print("3. Click it to change to 'REMOTE MODE: ON'")
    print("4. Now safe to click screen for remote operation")
    print()
    print("=" * 70)
    
    def open_browser():
        time.sleep(2)
        webbrowser.open(f'http://localhost:{port}')
    
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    try:
        socketio.run(app, host='0.0.0.0', port=port, debug=False)
    except KeyboardInterrupt:
        print("\\n[CLEAN] Stopping server...")
    except Exception as e:
        print(f"[CLEAN] Server error: {e}")
    finally:
        is_streaming = False
        print("[CLEAN] Server stopped")