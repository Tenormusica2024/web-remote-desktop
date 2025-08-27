#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Remote Desktop for Cloud Run - Debug Version
Enhanced debugging for screen sharing issues
"""

import os
import json
import logging
from datetime import datetime
from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
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
debug_logs = []

def add_debug_log(message):
    timestamp = datetime.now().isoformat()
    debug_logs.append(f"{timestamp}: {message}")
    logger.info(f"DEBUG: {message}")
    if len(debug_logs) > 50:  # Keep only last 50 logs
        debug_logs.pop(0)

@app.route('/debug')
def debug_info():
    return jsonify({
        'connected_clients': len(connected_clients),
        'local_clients': len(local_clients),
        'debug_logs': debug_logs[-10:],  # Last 10 logs
        'current_screenshot_available': current_screenshot is not None,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/')
def index():
    html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Remote Desktop - Debug Version</title>
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
        .btn-debug { background: #9C27B0; color: white; }
        @keyframes blink { 0%, 50% { opacity: 1; } 51%, 100% { opacity: 0.5; } }
        .status { padding: 6px 10px; border-radius: 15px; font-size: 12px; }
        .connected { background: #4CAF50; color: white; }
        .disconnected { background: #F44336; color: white; }
        
        /* Desktop View */
        .desktop-container { 
            height: calc(100vh - 200px); 
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
        
        /* Debug Panel */
        .debug-panel {
            background: rgba(75, 0, 130, 0.9);
            padding: 15px;
            margin: 10px;
            border-radius: 8px;
            font-size: 12px;
            display: none;
        }
        .debug-panel.show { display: block; }
        .debug-log { 
            background: #222; 
            padding: 10px; 
            border-radius: 5px; 
            max-height: 200px; 
            overflow-y: scroll;
            margin-top: 10px;
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
        .feedback.debug { background: #9C27B0; }
        
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
    </style>
</head>
<body>
    <div class="header">
        <div class="title">🖥️ Remote Desktop - Debug Version</div>
        <div class="controls">
            <div id="status" class="status disconnected">CLOUD READY</div>
            <button id="remote-btn" class="btn btn-warning">⚠️ OFF</button>
            <button id="refresh-btn" class="btn btn-primary">🔄</button>
            <button id="debug-btn" class="btn btn-debug">🔍 DEBUG</button>
        </div>
    </div>
    
    <div id="debug-panel" class="debug-panel">
        <h4>🔍 Debug Information</h4>
        <div id="debug-status">Loading debug info...</div>
        <div id="debug-log" class="debug-log">
            <div>Debug log will appear here...</div>
        </div>
        <button onclick="requestDebugScreenshot()" class="btn btn-debug">📸 Force Screenshot</button>
        <button onclick="testConnection()" class="btn btn-debug">🔗 Test Connection</button>
    </div>
    
    <div class="desktop-container">
        <div id="setup-instructions" class="setup-box">
            <h3>📋 Debug Setup Instructions</h3>
            <div class="step">
                <strong>Connection Status:</strong><br>
                <span id="local-status">Waiting for local client...</span>
            </div>
            <div class="step">
                <strong>Debug Mode:</strong> Click 🔍 DEBUG button above for details
            </div>
            <div class="step">
                <strong>PC Client:</strong> Make sure remote-desktop-client.py is running
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
        let debugMode = false;
        
        const statusEl = document.getElementById('status');
        const remoteBtnEl = document.getElementById('remote-btn');
        const refreshBtnEl = document.getElementById('refresh-btn');
        const debugBtnEl = document.getElementById('debug-btn');
        const textboxEl = document.getElementById('textbox');
        const feedbackEl = document.getElementById('feedback');
        const localStatusEl = document.getElementById('local-status');
        const desktopScreenEl = document.getElementById('desktop-screen');
        const setupInstructionsEl = document.getElementById('setup-instructions');
        const clickModeBtnEl = document.getElementById('click-mode-btn');
        const debugPanelEl = document.getElementById('debug-panel');
        const debugStatusEl = document.getElementById('debug-status');
        const debugLogEl = document.getElementById('debug-log');
        
        function showMessage(msg, type = 'success') {
            console.log(`${type.toUpperCase()}: ${msg}`);
            feedbackEl.textContent = msg;
            feedbackEl.className = `feedback ${type} show`;
            setTimeout(() => feedbackEl.classList.remove('show'), 4000);
        }
        
        function updateDebugPanel() {
            if (debugMode) {
                fetch('/debug')
                    .then(response => response.json())
                    .then(data => {
                        debugStatusEl.innerHTML = `
                            <strong>Clients:</strong> ${data.connected_clients} | 
                            <strong>Local:</strong> ${data.local_clients} | 
                            <strong>Screenshot:</strong> ${data.current_screenshot_available ? 'Available' : 'None'}<br>
                            <strong>Time:</strong> ${data.timestamp}
                        `;
                        
                        debugLogEl.innerHTML = data.debug_logs.map(log => `<div>${log}</div>`).join('');
                        debugLogEl.scrollTop = debugLogEl.scrollHeight;
                    })
                    .catch(err => {
                        debugStatusEl.innerHTML = `<span style="color: red;">Debug fetch error: ${err}</span>`;
                    });
            }
        }
        
        // Debug panel toggle
        debugBtnEl.addEventListener('click', () => {
            debugMode = !debugMode;
            if (debugMode) {
                debugPanelEl.classList.add('show');
                debugBtnEl.textContent = '🔍 HIDE';
                updateDebugPanel();
                setInterval(updateDebugPanel, 2000);
            } else {
                debugPanelEl.classList.remove('show');
                debugBtnEl.textContent = '🔍 DEBUG';
            }
        });
        
        socket.on('connect', () => {
            connected = true;
            statusEl.textContent = 'CLOUD CONNECTED';
            statusEl.className = 'status connected';
            showMessage('Connected to Cloud Run!', 'success');
            console.log('Socket connected with transport:', socket.io.engine.transport.name);
        });
        
        socket.on('disconnect', () => {
            connected = false;
            statusEl.textContent = 'CLOUD DISCONNECTED';
            statusEl.className = 'status disconnected';
            showMessage('Disconnected from server', 'error');
        });
        
        socket.on('local_client_connected', () => {
            localClientConnected = true;
            localStatusEl.textContent = 'PC client connected ✅';
            localStatusEl.style.color = '#4CAF50';
            showMessage('PC client connected!', 'success');
            console.log('Local client connected - requesting screenshot');
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
            console.log('Screenshot received:', data.image ? 'YES' : 'NO');
            if (data.image) {
                desktopScreenEl.src = 'data:image/jpeg;base64,' + data.image;
                desktopScreenEl.style.display = 'block';
                setupInstructionsEl.style.display = 'none';
                showMessage('📸 Screen updated!', 'success');
                console.log('Screenshot displayed successfully');
            } else {
                showMessage('📸 Screenshot empty!', 'error');
                console.log('Screenshot data was empty');
            }
        });
        
        socket.on('command_result', (data) => {
            showMessage(`${data.command}: ${data.success ? 'OK' : 'FAILED'}`, data.success ? 'success' : 'error');
        });
        
        socket.on('connect_error', (error) => {
            showMessage(`Connection error: ${error}`, 'error');
            console.error('Socket connection error:', error);
        });
        
        socket.on('error', (error) => {
            showMessage(`Socket error: ${error}`, 'error');
            console.error('Socket error:', error);
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
                showMessage('🔄 Refreshing screen...', 'debug');
                console.log('Manual refresh requested');
            } else {
                showMessage('❌ PC client not connected!', 'error');
            }
        });
        
        function requestDebugScreenshot() {
            console.log('Debug screenshot requested');
            socket.emit('request_screenshot');
            showMessage('📸 Debug screenshot requested', 'debug');
        }
        
        function testConnection() {
            console.log('Testing connection...');
            socket.emit('ping');
            showMessage('🔗 Connection test sent', 'debug');
        }
        
        socket.on('pong', () => {
            console.log('Pong received');
            showMessage('🔗 Connection test: OK', 'success');
        });
        
        // Click Mode Toggle
        clickModeBtnEl.addEventListener('click', () => {
            clickMode = !clickMode;
            if (clickMode) {
                clickModeBtnEl.textContent = '👆 ON';
                clickModeBtnEl.className = 'btn btn-success';
                desktopScreenEl.style.cursor = 'crosshair';
                showMessage('👆 Click mode ON', 'success');
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
        
        showMessage('🖥️ Debug version loaded!', 'debug');
        console.log('Debug version initialized');
        
        // Auto-refresh screen every 3 seconds when connected and remote mode is on
        setInterval(() => {
            if (localClientConnected && remoteMode) {
                socket.emit('request_screenshot');
                console.log('Auto-refresh screenshot requested');
            }
        }, 3000);
        
        // Log all socket events for debugging
        socket.onAny((eventName, ...args) => {
            console.log(`Socket event: ${eventName}`, args);
        });
    </script>
</body>
</html>"""
    return html

@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'version': 'cloudrun-debug',
        'clients': len(connected_clients),
        'local_clients': len(local_clients),
        'current_screenshot': current_screenshot is not None,
        'timestamp': datetime.now().isoformat()
    })

@socketio.on('connect')
def handle_connect():
    connected_clients.append(request.sid)
    add_debug_log(f"Web client connected: {request.sid} (Total: {len(connected_clients)})")
    emit('connection_confirmed', {
        'status': 'connected', 
        'client_id': request.sid,
        'server_time': datetime.now().isoformat()
    })

@socketio.on('disconnect')
def handle_disconnect():
    if request.sid in connected_clients:
        connected_clients.remove(request.sid)
        add_debug_log(f"Web client disconnected: {request.sid} (Remaining: {len(connected_clients)})")
    
    if request.sid in local_clients:
        local_clients.remove(request.sid)
        add_debug_log(f"Local client disconnected: {request.sid} (Remaining: {len(local_clients)})")
        emit('local_client_disconnected', broadcast=True)

@socketio.on('register_local_client')
def handle_register_local():
    if request.sid not in local_clients:
        local_clients.append(request.sid)
        add_debug_log(f"Local client registered: {request.sid} (Total local clients: {len(local_clients)})")
        emit('local_client_connected', broadcast=True)
        emit('registration_success', {'status': 'registered', 'client_id': request.sid})
    else:
        add_debug_log(f"Local client already registered: {request.sid}")
        emit('registration_success', {'status': 'already_registered', 'client_id': request.sid})

@socketio.on('send_command')
def handle_send_command(data):
    add_debug_log(f"Command received from {request.sid}: {data}")
    # Forward command to local clients only
    for client_id in local_clients:
        emit('execute_command', data, room=client_id)

@socketio.on('command_result')
def handle_command_result(data):
    add_debug_log(f"Command result from {request.sid}: {data}")
    # Forward result back to web clients only
    for client_id in connected_clients:
        if client_id not in local_clients:
            emit('command_result', data, room=client_id)

@socketio.on('request_screenshot')
def handle_request_screenshot():
    add_debug_log(f"Screenshot request from {request.sid}")
    # Forward screenshot request to local clients
    for client_id in local_clients:
        emit('request_screenshot', room=client_id)
        add_debug_log(f"Screenshot request forwarded to local client {client_id}")

@socketio.on('screenshot_data')
def handle_screenshot_data(data):
    global current_screenshot
    current_screenshot = data.get('image')
    add_debug_log(f"Screenshot received from local client {request.sid}, size: {len(current_screenshot) if current_screenshot else 0}")
    
    # Forward screenshot to web clients only
    web_client_count = 0
    for client_id in connected_clients:
        if client_id not in local_clients:
            emit('screenshot_data', data, room=client_id)
            web_client_count += 1
    
    add_debug_log(f"Screenshot forwarded to {web_client_count} web clients")

@socketio.on('ping')
def handle_ping():
    add_debug_log(f"Ping from {request.sid}")
    emit('pong')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    add_debug_log(f"Starting Cloud Run Remote Desktop (Debug) on port {port}")
    try:
        socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)
    except Exception as e:
        add_debug_log(f"Failed to start server: {e}")
        raise