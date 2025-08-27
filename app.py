#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Remote Desktop for Cloud Run - With Screen Display
"""

import os
import json
import logging
import base64
from datetime import datetime
from flask import Flask, jsonify, request, Response
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
latest_screenshot = None  # Store latest screenshot
latest_jpeg_bytes = None  # JPEG bytes cache for HTTP fallback

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
        .container { height: calc(100vh - 160px); display: flex; justify-content: center; align-items: center; background: #000; position: relative; }
        .screen-container { width: 100%; height: 100%; display: flex; justify-content: center; align-items: center; position: relative; }
        .screen-image { max-width: 90%; max-height: 90%; border: 2px solid #4CAF50; border-radius: 8px; display: none; }
        .no-screen { background: rgba(45, 55, 72, 0.9); padding: 30px; border-radius: 15px; text-align: center; max-width: 600px; }
        .no-screen h2 { color: #4CAF50; margin-bottom: 20px; }
        .toolbar { position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); background: rgba(0,0,0,0.8); padding: 10px; border-radius: 10px; display: flex; gap: 8px; flex-wrap: wrap; justify-content: center; }
        .toolbar input { padding: 8px; border: 1px solid #555; border-radius: 4px; background: #222; color: white; width: 280px; margin-bottom: 5px; }
        .btn-send { background: #4CAF50 !important; color: white !important; font-weight: bold !important; padding: 10px 16px !important; font-size: 14px !important; }
        .btn-enter { background: #2196F3 !important; color: white !important; font-weight: bold !important; padding: 10px 16px !important; font-size: 14px !important; }
        .feedback { position: fixed; top: 100px; right: 20px; padding: 15px; border-radius: 5px; max-width: 400px; opacity: 0; transition: opacity 0.3s; z-index: 1000; }
        .feedback.show { opacity: 1; }
        .feedback.success { background: #4CAF50; }
        .feedback.error { background: #F44336; }
        .screen-status { position: absolute; top: 10px; left: 10px; background: rgba(0,0,0,0.7); padding: 8px 12px; border-radius: 5px; font-size: 12px; z-index: 100; }
    </style>
</head>
<body>
    <div class="header">
        <div class="title">🌐 Remote Desktop - Cloud Run Edition</div>
        <div class="controls">
            <div id="status" class="status disconnected">CLOUD READY</div>
            <div id="local-status" class="status disconnected">PC CLIENT: OFF</div>
            <button id="remote-btn" class="btn btn-warning">⚠️ REMOTE MODE: OFF</button>
            <button id="screenshot-btn" class="btn btn-primary">📷 REFRESH SCREEN</button>
        </div>
    </div>
    
    <div class="container">
        <div class="screen-container">
            <div id="screen-status" class="screen-status">Waiting for PC screen...</div>
            <img id="screen-image" class="screen-image" alt="PC Screen">
            <div id="no-screen" class="no-screen">
                <h2>🖥️ PC Screen Display</h2>
                <p>📡 Waiting for PC client connection...</p>
                <div style="margin: 20px 0;">
                    <div>✅ Cloud Run Server: Connected</div>
                    <div id="pc-status">❌ PC Client: Not Connected</div>
                    <div id="screen-status-text">📺 Screen: No Data</div>
                </div>
                <p style="font-size: 14px; opacity: 0.8;">
                    Run the PC client and it will automatically send screen updates
                </p>
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
        const localStatusEl = document.getElementById('local-status');
        const remoteBtnEl = document.getElementById('remote-btn');
        const screenshotBtnEl = document.getElementById('screenshot-btn');
        const textboxEl = document.getElementById('textbox');
        const feedbackEl = document.getElementById('feedback');
        const screenImageEl = document.getElementById('screen-image');
        const noScreenEl = document.getElementById('no-screen');
        const screenStatusEl = document.getElementById('screen-status');
        const pcStatusEl = document.getElementById('pc-status');
        const screenStatusTextEl = document.getElementById('screen-status-text');
        
        function showMessage(msg, type = 'success') {
            feedbackEl.textContent = msg;
            feedbackEl.className = `feedback ${type} show`;
            setTimeout(() => feedbackEl.classList.remove('show'), 4000);
        }
        
        function updateScreenDisplay(hasScreen) {
            if (hasScreen) {
                screenImageEl.style.display = 'block';
                noScreenEl.style.display = 'none';
                screenStatusEl.textContent = 'PC Screen Active';
                screenStatusEl.style.background = 'rgba(76, 175, 80, 0.8)';
            } else {
                screenImageEl.style.display = 'none';
                noScreenEl.style.display = 'block';
                screenStatusEl.textContent = 'No Screen Data';
                screenStatusEl.style.background = 'rgba(244, 67, 54, 0.8)';
            }
        }
        
        socket.on('connect', () => {
            connected = true;
            statusEl.textContent = 'CLOUD CONNECTED';
            statusEl.className = 'status connected';
            showMessage('Connected to Cloud Run server!', 'success');
            
            // Notify server that web client connected
            socket.emit('web_client_connected');
        });
        
        socket.on('disconnect', () => {
            connected = false;
            statusEl.textContent = 'CLOUD DISCONNECTED';
            statusEl.className = 'status disconnected';
            updateScreenDisplay(false);
        });
        
        socket.on('local_client_connected', () => {
            localClientConnected = true;
            localStatusEl.textContent = 'PC CLIENT: ON';
            localStatusEl.className = 'status connected';
            pcStatusEl.textContent = '✅ PC Client: Connected';
            pcStatusEl.style.color = '#4CAF50';
            showMessage('PC client connected!', 'success');
        });
        
        socket.on('local_client_disconnected', () => {
            localClientConnected = false;
            localStatusEl.textContent = 'PC CLIENT: OFF';
            localStatusEl.className = 'status disconnected';
            pcStatusEl.textContent = '❌ PC Client: Not Connected';
            pcStatusEl.style.color = '#F44336';
            screenStatusTextEl.textContent = '📺 Screen: No Data';
            updateScreenDisplay(false);
            showMessage('PC client disconnected!', 'error');
        });
        
        // SCREEN UPDATE EVENT - This is the key missing piece!
        socket.on('screen_update', (data) => {
            console.log('Screen update received, data length:', data.image ? data.image.length : 0);
            if (data.image) {
                screenImageEl.src = 'data:image/jpeg;base64,' + data.image;
                screenStatusTextEl.textContent = '📺 Screen: Live';
                screenStatusTextEl.style.color = '#4CAF50';
                updateScreenDisplay(true);
                showMessage('Screen updated!', 'success');
            }
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
        
        // Screenshot request
        screenshotBtnEl.addEventListener('click', () => {
            if (!localClientConnected) {
                showMessage('❌ PC client not connected!', 'error');
                return;
            }
            showMessage('📷 Requesting fresh screenshot...', 'success');
            socket.emit('request_screenshot');
        });
        
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
                showMessage('❌ PC client not connected!', 'error');
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
                showMessage('❌ PC client not connected!', 'error');
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
                showMessage('❌ PC client not connected!', 'error');
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
        
        // Initialize
        updateScreenDisplay(false);
        showMessage('🌐 Cloud Run Remote Desktop with Screen Display loaded', 'success');
    </script>
</body>
</html>"""
    return html

@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'version': 'cloudrun-with-screen',
        'clients': len(connected_clients),
        'local_clients': len(local_clients),
        'has_screenshot': latest_screenshot is not None,
        'timestamp': datetime.now().isoformat()
    })

# HTTP Fallback: Direct JPEG frame access
@app.route('/frame.jpg')
def get_frame():
    """HTTP fallback for screen frame - bypasses Socket.IO"""
    global latest_jpeg_bytes
    if latest_jpeg_bytes:
        return Response(latest_jpeg_bytes, mimetype='image/jpeg')
    return ('', 204)

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

# NEW: Handle screen updates from PC client
@socketio.on('screen_update')
def handle_screen_update(data):
    global latest_screenshot, latest_jpeg_bytes
    b64 = (data or {}).get('image')
    if b64:
        latest_screenshot = b64
        logger.info(f"Screen update received from {request.sid}, image size: {len(b64)}")
        
        # Cache JPEG bytes for HTTP fallback
        try:
            latest_jpeg_bytes = base64.b64decode(b64.split(',', 1)[-1] if ',' in b64 else b64)
            logger.info(f"JPEG bytes cached: {len(latest_jpeg_bytes)} bytes")
        except Exception as e:
            logger.error(f"Failed to decode base64 image: {e}")
        
        # Forward to web clients only (not back to local clients)
        for client_id in connected_clients:
            if client_id not in local_clients:
                emit('screen_update', data, room=client_id)
                logger.info(f"Screen update forwarded to web client {client_id}")
    else:
        logger.warning(f"Screen update received without image data from {request.sid}")

# NEW: Handle web client connected event
@socketio.on('web_client_connected')
def handle_web_client_connected():
    logger.info(f"Web client reload detected: {request.sid}")
    
    # Send latest screenshot if available
    if latest_screenshot:
        emit('screen_update', {'image': latest_screenshot})
        logger.info(f"Sent cached screenshot to web client {request.sid}")
    
    # Notify local clients about web client connection
    for client_id in local_clients:
        emit('web_client_connected', room=client_id)
        logger.info(f"Notified local client {client_id} of web reload")

# NEW: Handle screenshot requests
@socketio.on('request_screenshot')
def handle_screenshot_request():
    logger.info(f"Screenshot request from web client: {request.sid}")
    # Forward to local clients
    for client_id in local_clients:
        emit('screenshot_request', room=client_id)

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
        if client_id not in local_clients:  # Don't send back to local clients
            emit('command_result', data, room=client_id)

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
    logger.info(f"Starting Cloud Run Remote Desktop (With Screen Display) on port {port}")
    try:
        socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise