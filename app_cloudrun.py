#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Remote Desktop for Cloud Run - Proxy Mode
Cloud Runでは直接画面操作はできないため、WebSocket経由でローカルPCに指示を送信
"""

import os
import json
import time
import logging
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'CloudRunRemoteDesktop2024!')
socketio = SocketIO(app, cors_allowed_origins="*")

# Global state
clients = []

@app.route('/')
def index():
    html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Remote Desktop - Cloud Run Edition</title>
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
        .connected { background: #4CAF50; color: white; }
        .disconnected { background: #F44336; color: white; }
        .container { height: calc(100vh - 80px); display: flex; justify-content: center; align-items: center; background: #000; }
        .proxy-mode { text-align: center; color: #888; padding: 40px; }
        .proxy-mode h2 { color: #4CAF50; margin-bottom: 20px; }
        .connection-box { background: rgba(45, 55, 72, 0.9); padding: 30px; border-radius: 15px; max-width: 600px; }
        .toolbar { position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); background: rgba(0,0,0,0.8); padding: 10px; border-radius: 10px; display: flex; gap: 8px; flex-wrap: wrap; justify-content: center; }
        .toolbar input { padding: 8px; border: 1px solid #555; border-radius: 4px; background: #222; color: white; width: 280px; margin-bottom: 5px; }
        .btn-send { background: #4CAF50 !important; color: white !important; font-weight: bold !important; padding: 10px 16px !important; font-size: 14px !important; }
        .btn-enter { background: #2196F3 !important; color: white !important; font-weight: bold !important; padding: 10px 16px !important; font-size: 14px !important; }
        .feedback { position: fixed; top: 100px; left: 20px; padding: 15px; border-radius: 5px; max-width: 400px; opacity: 0; transition: opacity 0.3s; }
        .feedback.show { opacity: 1; }
        .feedback.success { background: #4CAF50; }
        .feedback.error { background: #F44336; }
        .instruction { background: #1976D2; padding: 15px; margin: 15px 0; border-radius: 8px; }
        .step { margin: 10px 0; padding: 10px; background: rgba(255,255,255,0.1); border-radius: 5px; }
    </style>
</head>
<body>
    <div class="header">
        <div class="title">🌐 Remote Desktop - Cloud Run Edition</div>
        <div class="controls">
            <div id="status" class="status disconnected">CLOUD READY</div>
            <button id="remote-btn" class="btn btn-warning">⚠️ REMOTE MODE: OFF</button>
        </div>
    </div>
    
    <div class="container">
        <div class="connection-box">
            <div class="proxy-mode">
                <h2>🚀 Cloud Run Remote Desktop</h2>
                <div class="instruction">
                    <h3>📋 Setup Instructions:</h3>
                    <div class="step">
                        <strong>1. Download Local Client:</strong><br>
                        <a href="#" onclick="downloadClient()" style="color: #4CAF50;">Download remote-client.py</a>
                    </div>
                    <div class="step">
                        <strong>2. Run on your PC:</strong><br>
                        <code>python remote-client.py --server=CLOUD_RUN_URL</code>
                    </div>
                    <div class="step">
                        <strong>3. Turn ON Remote Mode above</strong>
                    </div>
                    <div class="step">
                        <strong>4. Use toolbar below to control your PC</strong>
                    </div>
                </div>
                <p>🔗 <strong>Connection Status:</strong> <span id="local-status">Waiting for local client...</span></p>
            </div>
        </div>
    </div>
    
    <div class="toolbar">
        <input type="text" id="textbox" placeholder="Type text to send to your PC">
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
        let localClientConnected = false;
        
        const statusEl = document.getElementById('status');
        const remoteBtnEl = document.getElementById('remote-btn');
        const textboxEl = document.getElementById('textbox');
        const feedbackEl = document.getElementById('feedback');
        const localStatusEl = document.getElementById('local-status');
        
        function showMessage(msg, type = 'success') {
            feedbackEl.textContent = msg;
            feedbackEl.className = `feedback ${type} show`;
            setTimeout(() => feedbackEl.classList.remove('show'), 4000);
        }
        
        socket.on('connect', () => {
            connected = true;
            statusEl.textContent = 'CLOUD CONNECTED';
            statusEl.className = 'status connected';
            showMessage('Connected to Cloud Run server!', 'success');
        });
        
        socket.on('disconnect', () => {
            connected = false;
            statusEl.textContent = 'CLOUD DISCONNECTED';
            statusEl.className = 'status disconnected';
        });
        
        socket.on('local_client_connected', () => {
            localClientConnected = true;
            localStatusEl.textContent = 'Local PC client connected ✅';
            localStatusEl.style.color = '#4CAF50';
            showMessage('Local PC client connected!', 'success');
        });
        
        socket.on('local_client_disconnected', () => {
            localClientConnected = false;
            localStatusEl.textContent = 'Local PC client disconnected ❌';
            localStatusEl.style.color = '#F44336';
            showMessage('Local PC client disconnected!', 'error');
        });
        
        socket.on('command_result', (data) => {
            showMessage(`${data.command}: ${data.success ? 'SUCCESS' : 'FAILED'}`, data.success ? 'success' : 'error');
        });
        
        // Remote Mode Toggle
        remoteBtnEl.addEventListener('click', () => {
            remoteMode = !remoteMode;
            if (remoteMode) {
                remoteBtnEl.textContent = '✅ REMOTE MODE: ON';
                remoteBtnEl.className = 'btn btn-primary';
                showMessage('✅ REMOTE MODE ON: Safe to send commands!', 'success');
            } else {
                remoteBtnEl.textContent = '⚠️ REMOTE MODE: OFF';
                remoteBtnEl.className = 'btn btn-warning';
                showMessage('⚠️ REMOTE MODE OFF: Commands disabled!', 'error');
            }
        });
        
        // Enhanced text sending
        function sendTextToRemote() {
            const text = textboxEl.value.trim();
            if (!text) {
                showMessage('⚠️ Please enter text first!', 'error');
                return;
            }
            if (!remoteMode) {
                showMessage('⚠️ Turn ON Remote Mode first!', 'error');
                return;
            }
            if (!localClientConnected) {
                showMessage('❌ Local PC client not connected!', 'error');
                return;
            }
            
            showMessage(`📤 Sending: "${text.substring(0, 20)}..."`, 'success');
            socket.emit('send_command', {
                command: 'type',
                data: { text: text }
            });
            textboxEl.value = '';
        }
        
        function sendEnterKey() {
            if (!remoteMode) {
                showMessage('⚠️ Turn ON Remote Mode first!', 'error');
                return;
            }
            if (!localClientConnected) {
                showMessage('❌ Local PC client not connected!', 'error');
                return;
            }
            
            showMessage('⏎ Sending Enter key', 'success');
            socket.emit('send_command', {
                command: 'key',
                data: { key: 'enter' }
            });
        }
        
        function sendKey(keyName) {
            if (!remoteMode) {
                showMessage('⚠️ Turn ON Remote Mode first!', 'error');
                return;
            }
            if (!localClientConnected) {
                showMessage('❌ Local PC client not connected!', 'error');
                return;
            }
            
            showMessage(`🎮 Sending: ${keyName}`, 'success');
            socket.emit('send_command', {
                command: 'key',
                data: { key: keyName }
            });
        }
        
        // Event listeners
        document.getElementById('send-btn').addEventListener('click', sendTextToRemote);
        document.getElementById('enter-btn').addEventListener('click', sendEnterKey);
        document.getElementById('ctrl-c-btn').addEventListener('click', () => sendKey('ctrl+c'));
        document.getElementById('ctrl-v-btn').addEventListener('click', () => sendKey('ctrl+v'));
        
        textboxEl.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                sendTextToRemote();
            }
        });
        
        function downloadClient() {
            const clientCode = `#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Remote Desktop Client for Cloud Run"""

import socketio
import pyautogui
import sys
import time

# Security settings
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1

class RemoteClient:
    def __init__(self, server_url):
        self.sio = socketio.Client()
        self.server_url = server_url
        self.setup_events()
    
    def setup_events(self):
        @self.sio.event
        def connect():
            print("Connected to Cloud Run server")
            self.sio.emit('register_local_client')
        
        @self.sio.event
        def disconnect():
            print("Disconnected from server")
        
        @self.sio.event
        def execute_command(data):
            try:
                command = data.get('command')
                cmd_data = data.get('data', {})
                
                if command == 'type':
                    text = cmd_data.get('text', '')
                    if text:
                        pyautogui.write(text, interval=0.05)
                        self.sio.emit('command_result', {'command': 'TYPE', 'success': True})
                        print(f"Typed: {text}")
                
                elif command == 'key':
                    key = cmd_data.get('key', '')
                    if key:
                        pyautogui.press(key)
                        self.sio.emit('command_result', {'command': f'KEY({key})', 'success': True})
                        print(f"Key pressed: {key}")
                
                elif command == 'click':
                    x = cmd_data.get('x', 0)
                    y = cmd_data.get('y', 0)
                    pyautogui.click(x, y)
                    self.sio.emit('command_result', {'command': f'CLICK({x},{y})', 'success': True})
                    print(f"Clicked: {x}, {y}")
                    
            except Exception as e:
                print(f"Command error: {e}")
                self.sio.emit('command_result', {'command': command.upper(), 'success': False})
    
    def connect(self):
        try:
            self.sio.connect(self.server_url)
            self.sio.wait()
        except Exception as e:
            print(f"Connection error: {e}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python remote-client.py --server=CLOUD_RUN_URL")
        sys.exit(1)
    
    server_url = sys.argv[1].replace('--server=', '')
    client = RemoteClient(server_url)
    client.connect()
`;
            
            const blob = new Blob([clientCode], { type: 'text/plain' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = 'remote-client.py';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            showMessage('📥 Client downloaded! Run on your PC', 'success');
        }
        
        showMessage('🌐 Cloud Run Remote Desktop loaded', 'success');
    </script>
</body>
</html>"""
    return html

@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'version': 'cloudrun',
        'clients': len(clients),
        'timestamp': datetime.now().isoformat()
    })

@socketio.on('connect')
def handle_connect():
    clients.append(request.sid)
    print(f"[CLOUD] Client connected: {request.sid} (Total: {len(clients)})")

@socketio.on('disconnect')
def handle_disconnect():
    if request.sid in clients:
        clients.remove(request.sid)
        print(f"[CLOUD] Client disconnected: {request.sid} (Remaining: {len(clients)})")

@socketio.on('register_local_client')
def handle_register_local():
    print(f"[CLOUD] Local client registered: {request.sid}")
    emit('local_client_connected', broadcast=True)

@socketio.on('send_command')
def handle_send_command(data):
    print(f"[CLOUD] Command received: {data}")
    # Forward command to local client
    emit('execute_command', data, broadcast=True)

@socketio.on('command_result')
def handle_command_result(data):
    print(f"[CLOUD] Command result: {data}")
    # Forward result back to web clients
    emit('command_result', data, broadcast=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    logging.info(f"Starting Cloud Run Remote Desktop on port {port}")
    try:
        socketio.run(app, host='0.0.0.0', port=port, debug=False, log_output=True)
    except Exception as e:
        logging.error(f"Failed to start server: {e}")
        raise