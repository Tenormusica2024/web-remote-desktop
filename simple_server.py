#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Remote Desktop Server - Minimal version with guaranteed remote mode button
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
app.config['SECRET_KEY'] = 'ClaudeRemoteDesktop2024!'
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
    return '''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chrome Remote Desktop代替 - Web版</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; background: #1a1a1a; color: #fff; overflow: hidden; }
        .header { background: #2d3748; padding: 10px 20px; display: flex; justify-content: space-between; align-items: center; }
        .title { font-size: 18px; font-weight: bold; color: #4299e1; }
        .controls { display: flex; gap: 10px; align-items: center; }
        .status { padding: 5px 10px; border-radius: 20px; font-size: 12px; font-weight: bold; }
        .status.connected { background: #38a169; color: white; }
        .status.disconnected { background: #e53e3e; color: white; }
        .btn { padding: 8px 16px; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; }
        .btn-primary { background: #4299e1; color: white; }
        .btn-secondary { background: #718096; color: white; }
        .remote-mode-warning { background: #e53e3e; animation: pulse 2s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.7; } }
        .desktop-container { position: relative; width: 100vw; height: calc(100vh - 60px); background: #000; display: flex; align-items: center; justify-content: center; }
        #desktop-screen { max-width: 100%; max-height: 100%; cursor: crosshair; border: 2px solid #4299e1; border-radius: 8px; }
        .loading { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center; color: #a0aec0; }
        .loading .spinner { width: 40px; height: 40px; border: 4px solid #2d3748; border-top: 4px solid #4299e1; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 20px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .toolbar { position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); background: rgba(45, 55, 72, 0.95); padding: 10px 20px; border-radius: 25px; display: flex; gap: 10px; }
        .toolbar input { padding: 8px 12px; border: 1px solid #4a5568; border-radius: 6px; background: #2d3748; color: white; min-width: 200px; }
        .feedback { position: fixed; top: 70px; left: 20px; background: rgba(45, 55, 72, 0.95); padding: 10px 15px; border-radius: 8px; transition: all 0.3s; opacity: 0; }
        .feedback.show { opacity: 1; }
        .feedback.success { border-left: 4px solid #38a169; }
        .feedback.error { border-left: 4px solid #e53e3e; }
    </style>
</head>
<body>
    <div class="header">
        <div class="title">Remote Desktop - Web Version</div>
        <div class="controls">
            <div id="status" class="status disconnected">Disconnected</div>
            <button id="remote-mode-btn" class="btn btn-secondary remote-mode-warning">Remote Mode: OFF</button>
            <button id="fullscreen-btn" class="btn btn-secondary">Fullscreen</button>
            <button id="refresh-btn" class="btn btn-primary">Refresh</button>
        </div>
    </div>
    
    <div class="desktop-container">
        <div class="loading" id="loading">
            <div class="spinner"></div>
            <div>Connecting to remote desktop...</div>
        </div>
        <img id="desktop-screen" style="display: none;" alt="Remote Desktop Screen" tabindex="0">
    </div>
    
    <div class="toolbar">
        <input type="text" id="text-input" placeholder="Type text here and press Enter to send to remote PC">
        <button id="send-text" class="btn btn-primary">Send</button>
        <button id="ctrl-c" class="btn btn-secondary">Ctrl+C</button>
        <button id="ctrl-v" class="btn btn-secondary">Ctrl+V</button>
        <button id="enter" class="btn btn-secondary">Enter</button>
    </div>
    
    <div id="feedback" class="feedback"></div>

    <script>
        const socket = io();
        const statusElement = document.getElementById('status');
        const loadingElement = document.getElementById('loading');
        const screenElement = document.getElementById('desktop-screen');
        const textInput = document.getElementById('text-input');
        const feedbackElement = document.getElementById('feedback');
        
        let isConnected = false;
        let screenWidth = 0;
        let screenHeight = 0;
        let remoteMode = false;
        
        function showFeedback(message, type = 'success') {
            feedbackElement.textContent = message;
            feedbackElement.className = `feedback ${type} show`;
            setTimeout(() => { feedbackElement.classList.remove('show'); }, 3000);
        }
        
        socket.on('connect', () => { console.log('Connected to remote desktop server'); });
        
        socket.on('connected', (data) => {
            isConnected = true;
            screenWidth = data.screen_width;
            screenHeight = data.screen_height;
            statusElement.textContent = 'Connected';
            statusElement.className = 'status connected';
            loadingElement.style.display = 'none';
            screenElement.style.display = 'block';
            showFeedback(`Connected to remote desktop (${screenWidth}x${screenHeight})`);
            setTimeout(() => { showFeedback('IMPORTANT: Turn ON Remote Mode to avoid same-PC interference!', 'error'); }, 2000);
        });
        
        socket.on('disconnect', () => {
            isConnected = false;
            statusElement.textContent = 'Disconnected';
            statusElement.className = 'status disconnected';
            screenElement.style.display = 'none';
            loadingElement.style.display = 'block';
            showFeedback('Connection lost', 'error');
        });
        
        socket.on('screenshot', (data) => {
            if (data.image) { screenElement.src = data.image; }
        });
        
        socket.on('action_result', (data) => {
            const { action, success } = data;
            if (success) { showFeedback(`${action} operation completed`); }
            else { showFeedback(`${action} operation failed`, 'error'); }
        });
        
        screenElement.addEventListener('click', (e) => {
            if (!isConnected) return;
            
            if (remoteMode) {
                e.preventDefault();
                e.stopImmediatePropagation();
                
                const rect = screenElement.getBoundingClientRect();
                const x = Math.round((e.clientX - rect.left) * (screenWidth / rect.width));
                const y = Math.round((e.clientY - rect.top) * (screenHeight / rect.height));
                
                socket.emit('click', { x, y });
                showFeedback('Remote PC operation (safe mode)', 'success');
            } else {
                showFeedback('WARNING: Turn ON Remote Mode first!', 'error');
            }
        });
        
        screenElement.addEventListener('wheel', (e) => {
            if (!isConnected) return;
            e.preventDefault();
            const rect = screenElement.getBoundingClientRect();
            const x = Math.round((e.clientX - rect.left) * (screenWidth / rect.width));
            const y = Math.round((e.clientY - rect.top) * (screenHeight / rect.height));
            const direction = e.deltaY > 0 ? -3 : 3;
            socket.emit('scroll', { x, y, direction });
        });
        
        textInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') { sendText(); }
        });
        
        function sendText() {
            const text = textInput.value;
            if (text && isConnected) {
                socket.emit('type', { text });
                textInput.value = '';
            }
        }
        
        function sendKey(key) {
            if (isConnected) { socket.emit('key', { key }); }
        }
        
        document.getElementById('send-text').addEventListener('click', sendText);
        document.getElementById('ctrl-c').addEventListener('click', () => sendKey('ctrl+c'));
        document.getElementById('ctrl-v').addEventListener('click', () => sendKey('ctrl+v'));
        document.getElementById('enter').addEventListener('click', () => sendKey('enter'));
        
        document.getElementById('fullscreen-btn').addEventListener('click', () => {
            if (document.fullscreenElement) { document.exitFullscreen(); }
            else { document.documentElement.requestFullscreen(); }
        });
        
        document.getElementById('refresh-btn').addEventListener('click', () => { location.reload(); });
        
        // REMOTE MODE TOGGLE - CRITICAL BUTTON
        document.getElementById('remote-mode-btn').addEventListener('click', () => {
            remoteMode = !remoteMode;
            const btn = document.getElementById('remote-mode-btn');
            
            if (remoteMode) {
                btn.textContent = 'Remote Mode: ON';
                btn.className = 'btn btn-primary';
                screenElement.style.cursor = 'crosshair';
                showFeedback('Remote Mode ON: Screen operations sent to remote PC', 'success');
            } else {
                btn.textContent = 'Remote Mode: OFF';
                btn.className = 'btn btn-secondary remote-mode-warning';
                screenElement.style.cursor = 'default';
                showFeedback('Remote Mode OFF: Same-PC interference risk!', 'error');
            }
        });
        
        setTimeout(() => { if (!isConnected) { showFeedback('Connecting to server...', 'error'); } }, 3000);
        
        setInterval(() => {
            if (isConnected && !remoteMode) {
                showFeedback('WARNING: Turn ON Remote Mode to avoid same-PC issues', 'error');
            }
        }, 30000);
    </script>
</body>
</html>'''

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
    print("REMOTE DESKTOP - GUARANTEED REMOTE MODE BUTTON")
    print("=" * 60)
    print()
    port = 8085
    print(f"Access URL: http://localhost:{port}")
    print(f"LAN Access: http://192.168.3.3:{port}")
    print()
    print("CRITICAL: Look for 'Remote Mode: OFF' button in header!")
    print("Click it to turn ON before using remote desktop")
    print("This prevents same-PC interference issues")
    print()
    print("=" * 60)
    
    def open_browser():
        time.sleep(3)
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