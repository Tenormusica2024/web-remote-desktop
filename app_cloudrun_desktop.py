#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Remote Desktop for Cloud Run - With Screen Sharing
Full version with screen sharing and remote control
"""

import os
import json
import logging
from datetime import datetime
from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'CloudRunRemoteDesktop2024!')
socketio = SocketIO(
    app, 
    cors_allowed_origins="*", 
    logger=True, 
    engineio_logger=True,
    ping_timeout=60,
    ping_interval=25,
    async_mode='threading'
)

# Global state
connected_clients = []
local_clients = []
current_screenshot = None

@app.route('/')
def index():
    html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Remote Desktop - Cloud Run with Screen Sharing</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        body { margin: 0; font-family: Arial, sans-serif; background: #111; color: white; }
        .header { background: #333; padding: 15px; display: flex; justify-content: space-between; align-items: center; }
        .title { font-size: 18px; color: #4CAF50; }
        .controls { display: flex; gap: 10px; align-items: center; }
        .btn { padding: 8px 12px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; font-size: 12px; }
        .btn-primary { background: #2196F3; color: white; }
        .btn-warning { background: #FF5722; color: white; animation: blink 1s infinite; }
        .btn-success { background: #4CAF50; color: white; }
        @keyframes blink { 0%, 50% { opacity: 1; } 51%, 100% { opacity: 0.5; } }
        .status { padding: 6px 10px; border-radius: 15px; font-size: 12px; }
        .connected { background: #4CAF50; color: white; }
        .disconnected { background: #F44336; color: white; }
        
        /* Desktop View */
        .desktop-container { 
            height: calc(100vh - 140px); 
            background: #000; 
            display: flex;
            justify-content: center;
            align-items: center;
            position: relative;
        }
        .desktop-screen { 
            max-width: 100%; 
            max-height: 100%; 
            border: 2px solid #555;
            border-radius: 8px;
            cursor: crosshair;
        }
        .no-screen { 
            color: #777; 
            font-size: 16px; 
            text-align: center; 
        }
        
        /* Mobile Toolbar */
        .toolbar { 
            position: fixed; 
            bottom: 0; 
            left: 0;
            right: 0;
            background: rgba(0,0,0,0.95); 
            padding: 10px; 
            display: flex; 
            gap: 5px; 
            flex-wrap: wrap; 
            justify-content: center;
            border-top: 1px solid #333;
        }
        .toolbar input { 
            padding: 8px; 
            border: 1px solid #555; 
            border-radius: 4px; 
            background: #222; 
            color: white; 
            width: 200px; 
            margin-bottom: 5px; 
        }
        .btn-send { background: #4CAF50 !important; }
        .btn-enter { background: #2196F3 !important; }
        
        /* Feedback */
        .feedback { 
            position: fixed; 
            top: 80px; 
            left: 10px; 
            right: 10px;
            padding: 12px; 
            border-radius: 5px; 
            max-width: 400px; 
            opacity: 0; 
            transition: opacity 0.3s; 
            z-index: 1000;
            font-size: 14px;
        }
        .feedback.show { opacity: 1; }
        .feedback.success { background: #4CAF50; }
        .feedback.error { background: #F44336; }
        
        /* Connection Status */
        .connection-status {
            font-size: 12px;
            color: #999;
        }
        
        /* Setup Instructions */
        .setup-box { 
            background: rgba(45, 55, 72, 0.9); 
            padding: 20px; 
            border-radius: 10px; 
            max-width: 500px; 
            text-align: center; 
        }
        .setup-box h3 { color: #4CAF50; margin-bottom: 15px; }
        .step { 
            margin: 8px 0; 
            padding: 8px; 
            background: rgba(255,255,255,0.1); 
            border-radius: 5px; 
            font-size: 14px;
        }
        .download-btn { 
            background: #4CAF50; 
            color: white; 
            padding: 10px 15px; 
            border: none; 
            border-radius: 5px; 
            cursor: pointer; 
            font-weight: bold; 
            text-decoration: none; 
            display: inline-block; 
            margin: 5px; 
        }
        .download-btn:hover { background: #45a049; }
    </style>
</head>
<body>
    <div class="header">
        <div class="title">🖥️ Remote Desktop - Screen Sharing</div>
        <div class="controls">
            <div id="status" class="status disconnected">CLOUD READY</div>
            <button id="remote-btn" class="btn btn-warning">⚠️ OFF</button>
            <button id="refresh-btn" class="btn btn-primary">🔄 REFRESH</button>
        </div>
    </div>
    
    <div class="desktop-container">
        <div id="setup-instructions" class="setup-box">
            <h3>📋 Setup Instructions</h3>
            <div class="step">
                <strong>1. Download Enhanced Client:</strong><br>
                <button class="download-btn" onclick="downloadEnhancedClient()">📥 Download remote-desktop-client.py</button>
            </div>
            <div class="step">
                <strong>2. Run on your PC:</strong><br>
                <code style="background: #222; padding: 4px; border-radius: 3px;">python remote-desktop-client.py</code>
            </div>
            <div class="step">
                <strong>3. Connection Status:</strong><br>
                <span id="local-status">Waiting for local client...</span>
            </div>
        </div>
        <img id="desktop-screen" class="desktop-screen" style="display: none;" onclick="handleScreenClick(event)">
    </div>
    
    <div class="toolbar">
        <input type="text" id="textbox" placeholder="Type text to send to PC">
        <button id="send-btn" class="btn btn-primary btn-send">📤 TEXT</button>
        <button id="enter-btn" class="btn btn-primary btn-enter">⏎ ENTER</button>
        <button id="ctrl-c-btn" class="btn btn-primary">CTRL+C</button>
        <button id="ctrl-v-btn" class="btn btn-primary">CTRL+V</button>
        <button id="click-mode-btn" class="btn btn-primary">👆 CLICK</button>
    </div>
    
    <div id="feedback" class="feedback"></div>

    <script>
        const socket = io();
        let connected = false;
        let remoteMode = false;
        let localClientConnected = false;
        let clickMode = false;
        
        const statusEl = document.getElementById('status');
        const remoteBtnEl = document.getElementById('remote-btn');
        const refreshBtnEl = document.getElementById('refresh-btn');
        const textboxEl = document.getElementById('textbox');
        const feedbackEl = document.getElementById('feedback');
        const localStatusEl = document.getElementById('local-status');
        const desktopScreenEl = document.getElementById('desktop-screen');
        const setupInstructionsEl = document.getElementById('setup-instructions');
        const clickModeBtnEl = document.getElementById('click-mode-btn');
        
        function showMessage(msg, type = 'success') {
            feedbackEl.textContent = msg;
            feedbackEl.className = `feedback ${type} show`;
            setTimeout(() => feedbackEl.classList.remove('show'), 3000);
        }
        
        socket.on('connect', () => {
            connected = true;
            statusEl.textContent = 'CLOUD CONNECTED';
            statusEl.className = 'status connected';
            showMessage('Connected to Cloud Run!', 'success');
        });
        
        socket.on('disconnect', () => {
            connected = false;
            statusEl.textContent = 'CLOUD DISCONNECTED';
            statusEl.className = 'status disconnected';
        });
        
        socket.on('local_client_connected', () => {
            localClientConnected = true;
            localStatusEl.textContent = 'PC client connected ✅';
            localStatusEl.style.color = '#4CAF50';
            showMessage('PC client connected!', 'success');
            // Request initial screenshot
            socket.emit('request_screenshot');
        });
        
        socket.on('local_client_disconnected', () => {
            localClientConnected = false;
            localStatusEl.textContent = 'PC client disconnected ❌';
            localStatusEl.style.color = '#F44336';
            showMessage('PC client disconnected!', 'error');
            desktopScreenEl.style.display = 'none';
            setupInstructionsEl.style.display = 'block';
        });
        
        socket.on('screenshot_data', (data) => {
            if (data.image) {
                desktopScreenEl.src = 'data:image/jpeg;base64,' + data.image;
                desktopScreenEl.style.display = 'block';
                setupInstructionsEl.style.display = 'none';
            }
        });
        
        socket.on('command_result', (data) => {
            showMessage(`${data.command}: ${data.success ? 'OK' : 'FAILED'}`, data.success ? 'success' : 'error');
        });
        
        // Remote Mode Toggle
        remoteBtnEl.addEventListener('click', () => {
            remoteMode = !remoteMode;
            if (remoteMode) {
                remoteBtnEl.textContent = '✅ ON';
                remoteBtnEl.className = 'btn btn-success';
                showMessage('✅ REMOTE MODE ON', 'success');
            } else {
                remoteBtnEl.textContent = '⚠️ OFF';
                remoteBtnEl.className = 'btn btn-warning';
                showMessage('⚠️ REMOTE MODE OFF', 'error');
            }
        });
        
        // Refresh Screen
        refreshBtnEl.addEventListener('click', () => {
            if (localClientConnected) {
                socket.emit('request_screenshot');
                showMessage('🔄 Refreshing screen...', 'success');
            } else {
                showMessage('❌ PC client not connected!', 'error');
            }
        });
        
        // Click Mode Toggle
        clickModeBtnEl.addEventListener('click', () => {
            clickMode = !clickMode;
            if (clickMode) {
                clickModeBtnEl.textContent = '👆 CLICK ON';
                clickModeBtnEl.className = 'btn btn-success';
                desktopScreenEl.style.cursor = 'crosshair';
                showMessage('👆 Click mode ON - Tap screen to click', 'success');
            } else {
                clickModeBtnEl.textContent = '👆 CLICK';
                clickModeBtnEl.className = 'btn btn-primary';
                desktopScreenEl.style.cursor = 'default';
                showMessage('👆 Click mode OFF', 'success');
            }
        });
        
        function handleScreenClick(event) {
            if (!clickMode || !remoteMode || !localClientConnected) {
                if (!remoteMode) showMessage('⚠️ Turn ON Remote Mode first!', 'error');
                else if (!localClientConnected) showMessage('❌ PC client not connected!', 'error');
                else if (!clickMode) showMessage('👆 Turn ON Click Mode first!', 'error');
                return;
            }
            
            const rect = desktopScreenEl.getBoundingClientRect();
            const x = Math.round((event.clientX - rect.left) * (desktopScreenEl.naturalWidth / rect.width));
            const y = Math.round((event.clientY - rect.top) * (desktopScreenEl.naturalHeight / rect.height));
            
            showMessage(`👆 Clicking at ${x}, ${y}`, 'success');
            socket.emit('send_command', {
                command: 'click',
                data: { x: x, y: y }
            });
        }
        
        function sendTextToRemote() {
            const text = textboxEl.value.trim();
            if (!text) {
                showMessage('⚠️ Enter text first!', 'error');
                return;
            }
            if (!remoteMode) {
                showMessage('⚠️ Turn ON Remote Mode first!', 'error');
                return;
            }
            if (!localClientConnected) {
                showMessage('❌ PC client not connected!', 'error');
                return;
            }
            
            showMessage(`📤 Sending: "${text.substring(0, 15)}..."`, 'success');
            socket.emit('send_command', {
                command: 'type',
                data: { text: text }
            });
            textboxEl.value = '';
        }
        
        function sendKey(keyName) {
            if (!remoteMode) {
                showMessage('⚠️ Turn ON Remote Mode first!', 'error');
                return;
            }
            if (!localClientConnected) {
                showMessage('❌ PC client not connected!', 'error');
                return;
            }
            
            showMessage(`⌨️ ${keyName}`, 'success');
            socket.emit('send_command', {
                command: 'key',
                data: { key: keyName }
            });
        }
        
        // Event listeners
        document.getElementById('send-btn').addEventListener('click', sendTextToRemote);
        document.getElementById('enter-btn').addEventListener('click', () => sendKey('enter'));
        document.getElementById('ctrl-c-btn').addEventListener('click', () => sendKey('ctrl+c'));
        document.getElementById('ctrl-v-btn').addEventListener('click', () => sendKey('ctrl+v'));
        
        textboxEl.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                sendTextToRemote();
            }
        });
        
        function downloadEnhancedClient() {
            const clientCode = "#!/usr/bin/env python3\\n" +
"# -*- coding: utf-8 -*-\\n" +
"# Remote Desktop Client with Screen Sharing\\n\\n" +
"import socketio\\n" +
"import pyautogui\\n" +
"import base64\\n" +
"import io\\n" +
"import sys\\n" +
"import time\\n" +
"import logging\\n" +
"import threading\\n\\n" +
"# Security settings\\n" +
"pyautogui.FAILSAFE = True\\n" +
"pyautogui.PAUSE = 0.1\\n\\n" +
"logging.basicConfig(level=logging.INFO)\\n" +
"logger = logging.getLogger(__name__)\\n\\n" +
"class EnhancedRemoteClient:\\n" +
"    def __init__(self, server_url='https://remote-desktop-ycqe3vmjva-uc.a.run.app'):\\n" +
"        self.sio = socketio.Client()\\n" +
"        self.server_url = server_url\\n" +
"        self.setup_events()\\n\\n" +
"    def setup_events(self):\\n" +
"        @self.sio.event\\n" +
"        def connect():\\n" +
"            print('Connected to Cloud Run server')\\n" +
"            print(f'Server URL: {self.server_url}')\\n" +
"            self.sio.emit('register_local_client')\\n\\n" +
"        @self.sio.event\\n" +
"        def disconnect():\\n" +
"            print('Disconnected from server')\\n\\n" +
"        @self.sio.event\\n" +
"        def execute_command(data):\\n" +
"            try:\\n" +
"                command = data.get('command')\\n" +
"                cmd_data = data.get('data', {})\\n" +
"                print(f'Executing: {command} - {cmd_data}')\\n\\n" +
"                if command == 'type':\\n" +
"                    text = cmd_data.get('text', '')\\n" +
"                    if text:\\n" +
"                        pyautogui.write(text, interval=0.02)\\n" +
"                        self.sio.emit('command_result', {'command': 'TYPE', 'success': True})\\n" +
"                        print(f'Typed: {text}')\\n\\n" +
"                elif command == 'key':\\n" +
"                    key = cmd_data.get('key', '')\\n" +
"                    if key:\\n" +
"                        pyautogui.press(key)\\n" +
"                        self.sio.emit('command_result', {'command': f'KEY({key})', 'success': True})\\n" +
"                        print(f'Key: {key}')\\n\\n" +
"                elif command == 'click':\\n" +
"                    x = cmd_data.get('x', 0)\\n" +
"                    y = cmd_data.get('y', 0)\\n" +
"                    pyautogui.click(x, y)\\n" +
"                    self.sio.emit('command_result', {'command': f'CLICK({x},{y})', 'success': True})\\n" +
"                    print(f'Clicked: {x}, {y}')\\n\\n" +
"            except Exception as e:\\n" +
"                print(f'Command error: {e}')\\n" +
"                self.sio.emit('command_result', {'command': command.upper(), 'success': False})\\n\\n" +
"        @self.sio.event\\n" +
"        def request_screenshot():\\n" +
"            try:\\n" +
"                screenshot = pyautogui.screenshot()\\n" +
"                screenshot.thumbnail((1280, 720), resample=1)\\n" +
"                buffer = io.BytesIO()\\n" +
"                screenshot.save(buffer, format='JPEG', quality=70)\\n" +
"                img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')\\n" +
"                self.sio.emit('screenshot_data', {'image': img_base64})\\n" +
"                print('Screenshot sent')\\n" +
"            except Exception as e:\\n" +
"                print(f'Screenshot error: {e}')\\n\\n" +
"    def connect(self):\\n" +
"        try:\\n" +
"            print(f'Connecting to {self.server_url}...')\\n" +
"            self.sio.connect(self.server_url, transports=['websocket', 'polling'])\\n" +
"            print('Connected! Screen sharing active...')\\n" +
"            self.sio.wait()\\n" +
"        except Exception as e:\\n" +
"            print(f'Connection error: {e}')\\n\\n" +
"if __name__ == '__main__':\\n" +
"    print('=============================================================')\\n" +
"    print('  Remote Desktop Client - Enhanced with Screen Sharing')\\n" +
"    print('=============================================================')\\n" +
"    client = EnhancedRemoteClient()\\n" +
"    client.connect()\\n";
            
            const blob = new Blob([clientCode], { type: 'text/plain' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = 'remote-desktop-client.py';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            showMessage('📥 Enhanced client downloaded!', 'success');
        }
        
        showMessage('🖥️ Screen sharing ready!', 'success');
        
        // Auto-refresh screen every 2 seconds when connected
        setInterval(() => {
            if (localClientConnected && remoteMode) {
                socket.emit('request_screenshot');
            }
        }, 2000);
    </script>
</body>
</html>"""
    return html

@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'version': 'cloudrun-desktop-sharing',
        'clients': len(connected_clients),
        'local_clients': len(local_clients),
        'timestamp': datetime.now().isoformat()
    })

@socketio.on('connect')
def handle_connect():
    connected_clients.append(request.sid)
    client_info = {
        'client_id': request.sid,
        'namespace': request.namespace,
        'transport': getattr(request, 'transport', {}).get('name', 'unknown') if hasattr(request, 'transport') else 'unknown',
        'timestamp': datetime.now().isoformat()
    }
    logger.info(f"Client connected: {request.sid} | Transport: {client_info['transport']} | Total: {len(connected_clients)}")
    emit('connection_confirmed', {
        'status': 'connected', 
        'client_id': request.sid,
        'transport': client_info['transport'],
        'server_time': datetime.now().isoformat()
    })

@socketio.on('disconnect')
def handle_disconnect():
    if request.sid in connected_clients:
        connected_clients.remove(request.sid)
        logger.info(f"Web client disconnected: {request.sid} (Remaining: {len(connected_clients)})")
    
    if request.sid in local_clients:
        local_clients.remove(request.sid)
        logger.info(f"Local client disconnected: {request.sid} (Remaining: {len(local_clients)})")
        emit('local_client_disconnected', broadcast=True)

@socketio.on('register_local_client')
def handle_register_local():
    if request.sid not in local_clients:
        local_clients.append(request.sid)
        logger.info(f"Local client registered: {request.sid} | Total local clients: {len(local_clients)}")
        emit('local_client_connected', broadcast=True)
        emit('registration_success', {'status': 'registered', 'client_id': request.sid})
    else:
        logger.info(f"Local client already registered: {request.sid}")
        emit('registration_success', {'status': 'already_registered', 'client_id': request.sid})

@socketio.on('send_command')
def handle_send_command(data):
    logger.info(f"Command received: {data}")
    # Forward command to local clients only
    for client_id in local_clients:
        emit('execute_command', data, room=client_id)

@socketio.on('command_result')
def handle_command_result(data):
    logger.info(f"Command result: {data}")
    # Forward result back to web clients only
    for client_id in connected_clients:
        if client_id not in local_clients:
            emit('command_result', data, room=client_id)

@socketio.on('request_screenshot')
def handle_request_screenshot():
    logger.info(f"Screenshot request from {request.sid}")
    # Forward screenshot request to local clients
    for client_id in local_clients:
        emit('request_screenshot', room=client_id)

@socketio.on('screenshot_data')
def handle_screenshot_data(data):
    logger.info(f"Screenshot received from local client")
    # Forward screenshot to web clients only
    for client_id in connected_clients:
        if client_id not in local_clients:
            emit('screenshot_data', data, room=client_id)

@socketio.on('ping')
def handle_ping():
    logger.debug(f"Ping from {request.sid}")
    emit('pong')

@socketio.on('client_heartbeat')
def handle_client_heartbeat(data):
    logger.debug(f"Heartbeat from {request.sid}: {data}")
    emit('server_heartbeat', {'server_time': datetime.now().isoformat(), 'client_id': request.sid})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"Starting Cloud Run Remote Desktop (Desktop Sharing) on port {port}")
    try:
        socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise