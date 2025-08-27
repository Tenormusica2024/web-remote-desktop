#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web Remote Desktop - Chrome Remote Desktop Alternative
Final version with embedded HTML to avoid template caching issues
"""

import os
import sys
import json
import time
import base64
import subprocess
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

# Embedded HTML with Remote Mode Button
HTML_CONTENT = '''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chrome Remote Desktop代替 - Web版</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #1a1a1a; color: #ffffff; overflow: hidden; }
        .header { background: #2d3748; padding: 10px 20px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 10px rgba(0,0,0,0.3); z-index: 1000; position: relative; }
        .title { font-size: 18px; font-weight: bold; color: #4299e1; }
        .controls { display: flex; gap: 10px; align-items: center; }
        .status { padding: 5px 10px; border-radius: 20px; font-size: 12px; font-weight: bold; }
        .status.connected { background: #38a169; color: white; }
        .status.disconnected { background: #e53e3e; color: white; }
        .btn { padding: 8px 16px; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; transition: all 0.2s; }
        .btn:hover { transform: translateY(-1px); }
        .btn-primary { background: #4299e1; color: white; }
        .btn-secondary { background: #718096; color: white; }
        .remote-mode-warning { background: linear-gradient(45deg, #e53e3e, #f56565); animation: pulse 2s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.7; } }
        .desktop-container { position: relative; width: 100vw; height: calc(100vh - 60px); overflow: hidden; background: #000; display: flex; align-items: center; justify-content: center; }
        #desktop-screen { max-width: 100%; max-height: 100%; cursor: crosshair; border: 2px solid #4299e1; border-radius: 8px; box-shadow: 0 4px 20px rgba(66, 153, 225, 0.3); outline: none; tabindex: 0; }
        #desktop-screen:focus { border-color: #38a169; box-shadow: 0 4px 20px rgba(56, 161, 105, 0.4); }
        .loading { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center; color: #a0aec0; }
        .loading .spinner { width: 40px; height: 40px; border: 4px solid #2d3748; border-top: 4px solid #4299e1; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 20px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .toolbar { position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); background: rgba(45, 55, 72, 0.95); padding: 10px 20px; border-radius: 25px; display: flex; gap: 10px; backdrop-filter: blur(10px); box-shadow: 0 4px 20px rgba(0,0,0,0.3); }
        .toolbar input { padding: 8px 12px; border: 1px solid #4a5568; border-radius: 6px; background: #2d3748; color: white; min-width: 200px; }
        .toolbar input:focus { outline: none; border-color: #4299e1; box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.1); }
        .key-shortcuts { position: fixed; top: 70px; right: 20px; background: rgba(45, 55, 72, 0.95); padding: 15px; border-radius: 10px; backdrop-filter: blur(10px); max-width: 250px; font-size: 12px; }
        .key-shortcuts h4 { color: #4299e1; margin-bottom: 10px; }
        .shortcut-item { display: flex; justify-content: space-between; margin-bottom: 5px; padding: 2px 0; }
        .feedback { position: fixed; top: 70px; left: 20px; background: rgba(45, 55, 72, 0.95); padding: 10px 15px; border-radius: 8px; backdrop-filter: blur(10px); transition: all 0.3s; opacity: 0; transform: translateY(-10px); }
        .feedback.show { opacity: 1; transform: translateY(0); }
        .feedback.success { border-left: 4px solid #38a169; }
        .feedback.error { border-left: 4px solid #e53e3e; }
    </style>
</head>
<body>
    <div class="header">
        <div class="title">🖥️ Chrome Remote Desktop代替 - Web版</div>
        <div class="controls">
            <div id="status" class="status disconnected">切断中</div>
            <button id="remote-mode-btn" class="btn btn-secondary remote-mode-warning">🚨 リモートモード: OFF</button>
            <button id="fullscreen-btn" class="btn btn-secondary">全画面</button>
            <button id="refresh-btn" class="btn btn-primary">画面更新</button>
        </div>
    </div>
    
    <div class="desktop-container">
        <div class="loading" id="loading">
            <div class="spinner"></div>
            <div>リモートデスクトップに接続中...</div>
        </div>
        <img id="desktop-screen" style="display: none;" alt="Remote Desktop Screen" tabindex="0">
    </div>
    
    <div class="toolbar">
        <input type="text" id="text-input" placeholder="ここにテキストを入力してEnterでリモートPCに送信">
        <button id="send-text" class="btn btn-primary">送信</button>
        <button id="ctrl-c" class="btn btn-secondary">Ctrl+C</button>
        <button id="ctrl-v" class="btn btn-secondary">Ctrl+V</button>
        <button id="enter" class="btn btn-secondary">Enter</button>
    </div>
    
    <div class="key-shortcuts">
        <h4>🎮 操作方法</h4>
        <div class="shortcut-item"><span>1. リモートモード</span><span>🚨 ボタンをONにする</span></div>
        <div class="shortcut-item"><span>2. 画面クリック</span><span>リモートPC操作開始</span></div>
        <div class="shortcut-item"><span>3. キーボード入力</span><span>緑枠内で直接タイプ</span></div>
        <div class="shortcut-item"><span>4. Claude Code</span><span>リモート経由で入力</span></div>
        <div class="shortcut-item"><span>⚠️ 同PC問題</span><span>リモートモード必須</span></div>
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
            setTimeout(() => { feedbackElement.classList.remove('show'); }, 2000);
        }
        
        socket.on('connect', () => { console.log('Connected to remote desktop server'); });
        
        socket.on('connected', (data) => {
            isConnected = true;
            screenWidth = data.screen_width;
            screenHeight = data.screen_height;
            statusElement.textContent = '接続済み';
            statusElement.className = 'status connected';
            loadingElement.style.display = 'none';
            screenElement.style.display = 'block';
            showFeedback(`リモートデスクトップに接続しました (${screenWidth}x${screenHeight})`);
            setTimeout(() => { showFeedback('🚨 同PC操作を回避するため、リモートモードをONにしてください！', 'error'); }, 2000);
        });
        
        socket.on('disconnect', () => {
            isConnected = false;
            statusElement.textContent = '切断中';
            statusElement.className = 'status disconnected';
            screenElement.style.display = 'none';
            loadingElement.style.display = 'block';
            showFeedback('接続が切断されました', 'error');
        });
        
        socket.on('screenshot', (data) => {
            if (data.image) { screenElement.src = data.image; }
        });
        
        socket.on('action_result', (data) => {
            const { action, success } = data;
            if (success) { showFeedback(`${action}操作が完了しました`); }
            else { showFeedback(`${action}操作に失敗しました`, 'error'); }
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
                screenElement.focus();
                screenElement.style.borderColor = '#38a169';
                screenElement.style.boxShadow = '0 4px 20px rgba(56, 161, 105, 0.6)';
                
                const dot = document.createElement('div');
                dot.style.cssText = `position: fixed; left: ${e.clientX - 5}px; top: ${e.clientY - 5}px; width: 10px; height: 10px; background: #38a169; border-radius: 50%; pointer-events: none; z-index: 1000; animation: clickFeedback 0.3s ease-out forwards;`;
                document.body.appendChild(dot);
                setTimeout(() => dot.remove(), 300);
                
                showFeedback('✅ リモートPC操作中（専用モード）', 'success');
            } else {
                showFeedback('🚨 リモートモードをONにして操作してください！', 'error');
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
        
        // 🚨 リモートモードトグル - 重要なボタン
        document.getElementById('remote-mode-btn').addEventListener('click', () => {
            remoteMode = !remoteMode;
            const btn = document.getElementById('remote-mode-btn');
            
            if (remoteMode) {
                btn.textContent = '✅ リモートモード: ON';
                btn.className = 'btn btn-primary';
                screenElement.style.cursor = 'crosshair';
                showFeedback('✅ リモートモードON: 画面操作がリモートPCに送信されます', 'success');
            } else {
                btn.textContent = '🚨 リモートモード: OFF';
                btn.className = 'btn btn-secondary remote-mode-warning';
                screenElement.style.cursor = 'default';
                screenElement.style.borderColor = '#4299e1';
                screenElement.style.boxShadow = '0 4px 20px rgba(66, 153, 225, 0.3)';
                showFeedback('🚨 リモートモードOFF: 同PC問題発生の危険！', 'error');
            }
        });
        
        screenElement.addEventListener('keydown', (e) => {
            if (!isConnected || !remoteMode) return;
            
            if (document.activeElement === screenElement && remoteMode) {
                e.preventDefault();
                e.stopPropagation();
                
                let keyToSend = e.key;
                if (e.ctrlKey && e.key === 'c') keyToSend = 'ctrl+c';
                else if (e.ctrlKey && e.key === 'v') keyToSend = 'ctrl+v';
                else if (e.ctrlKey && e.key === 'z') keyToSend = 'ctrl+z';
                else if (e.ctrlKey && e.key === 'y') keyToSend = 'ctrl+y';
                else if (e.ctrlKey && e.key === 'a') keyToSend = 'ctrl+a';
                else if (e.ctrlKey && e.key === 's') keyToSend = 'ctrl+s';
                else if (e.key === 'Enter') keyToSend = 'enter';
                else if (e.key === 'Backspace') keyToSend = 'backspace';
                else if (e.key === 'Tab') keyToSend = 'tab';
                else if (e.key === 'Escape') keyToSend = 'esc';
                else if (e.key === 'ArrowUp') keyToSend = 'up';
                else if (e.key === 'ArrowDown') keyToSend = 'down';
                else if (e.key === 'ArrowLeft') keyToSend = 'left';
                else if (e.key === 'ArrowRight') keyToSend = 'right';
                
                if (keyToSend.length === 1) { socket.emit('type', { text: keyToSend }); }
                else { socket.emit('key', { key: keyToSend }); }
                
                showFeedback(`キー入力: ${keyToSend}`);
            }
        });
        
        screenElement.addEventListener('mousedown', (e) => { e.preventDefault(); e.stopImmediatePropagation(); screenElement.focus(); });
        screenElement.addEventListener('mouseup', (e) => { e.preventDefault(); e.stopImmediatePropagation(); });
        screenElement.addEventListener('contextmenu', (e) => { e.preventDefault(); });
        
        screenElement.addEventListener('focus', (e) => {
            screenElement.style.borderColor = '#38a169';
            screenElement.style.boxShadow = '0 4px 20px rgba(56, 161, 105, 0.6)';
            showFeedback('キーボード入力モード: リモートPC操作中', 'success');
        });
        
        screenElement.addEventListener('blur', (e) => {
            screenElement.style.borderColor = '#4299e1';
            screenElement.style.boxShadow = '0 4px 20px rgba(66, 153, 225, 0.3)';
        });
        
        document.addEventListener('keydown', (e) => {
            if (document.activeElement !== screenElement) {
                if (e.key === 'F11') { e.preventDefault(); document.getElementById('fullscreen-btn').click(); }
            }
        });
        
        const style = document.createElement('style');
        style.textContent = `@keyframes clickFeedback { 0% { transform: scale(1); opacity: 1; } 100% { transform: scale(2); opacity: 0; } }`;
        document.head.appendChild(style);
        
        setTimeout(() => { if (!isConnected) { showFeedback('サーバーに接続中です...', 'error'); } }, 3000);
        
        setInterval(() => {
            if (isConnected && !remoteMode) {
                showFeedback('⚠️ 同PC問題回避のため、リモートモードをONにしてください', 'error');
            }
        }, 30000);
    </script>
</body>
</html>'''

@app.route('/')
def index():
    return HTML_CONTENT

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
    print("Chrome Remote Desktop Alternative - FINAL VERSION")
    print("=" * 60)
    print()
    print("Remote Mode Button Built-in Version")
    print("Remote Mode Button is displayed in the header")
    print()
    port = 8085
    print(f"Access URL: http://localhost:{port}")
    print(f"LAN Access: http://192.168.3.3:{port}")
    print()
    print("Important Usage Steps:")
    print("1. Access via browser")
    print("2. Click 'Remote Mode: OFF' button at top")
    print("3. Confirm it changes to 'Remote Mode: ON'")
    print("4. Click screen to start remote PC operation")
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