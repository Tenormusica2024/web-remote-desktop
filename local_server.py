#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Local Remote Desktop Server
Runs locally with ngrok tunnel for external access
"""

import os
import json
import logging
from datetime import datetime
from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit
import pyautogui
import argparse

# Security settings
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'LocalRemoteDesktop2024!'

# Socket.IO with fallback support for corporate networks
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=False,
    async_mode='threading'
)

# Global state
connected_clients = []

@app.route('/')
def index():
    html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Local Remote Desktop</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        body { margin: 0; font-family: Arial, sans-serif; background: #111; color: white; }
        .header { background: #333; padding: 15px; display: flex; justify-content: space-between; align-items: center; }
        .title { font-size: 20px; color: #4CAF50; }
        .status { padding: 8px 12px; border-radius: 20px; font-size: 14px; }
        .connected { background: #4CAF50; color: white; }
        .disconnected { background: #F44336; color: white; }
        .container { padding: 20px; max-width: 800px; margin: 0 auto; }
        .input-group { margin: 20px 0; }
        .input-group input { width: 100%; padding: 12px; font-size: 16px; border: 1px solid #555; background: #222; color: white; border-radius: 5px; }
        .btn-group { display: flex; gap: 10px; flex-wrap: wrap; }
        .btn { padding: 12px 20px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; font-size: 16px; }
        .btn-primary { background: #2196F3; color: white; }
        .btn-success { background: #4CAF50; color: white; }
        .btn-warning { background: #FF9800; color: white; }
        .feedback { padding: 15px; margin-top: 20px; border-radius: 5px; display: none; }
        .feedback.show { display: block; }
        .feedback.success { background: #4CAF50; }
        .feedback.error { background: #F44336; }
        .transport-info { margin-top: 10px; padding: 10px; background: rgba(255,255,255,0.1); border-radius: 5px; }
    </style>
</head>
<body>
    <div class="header">
        <div class="title">Local Remote Desktop - ngrok Ready</div>
        <div id="status" class="status disconnected">DISCONNECTED</div>
    </div>
    
    <div class="container">
        <h2>Remote Control Interface</h2>
        
        <div class="transport-info">
            <strong>Connection:</strong> <span id="transport">Detecting...</span>
            <br><small>(WebSocket = Fast, Polling = Corporate-friendly)</small>
        </div>
        
        <div class="input-group">
            <input type="text" id="textbox" placeholder="Type text to send to your PC" autofocus>
        </div>
        
        <div class="btn-group">
            <button class="btn btn-success" onclick="sendText()">Send Text</button>
            <button class="btn btn-primary" onclick="sendKey('enter')">Enter</button>
            <button class="btn btn-primary" onclick="sendKey('tab')">Tab</button>
            <button class="btn btn-warning" onclick="sendKey('escape')">Escape</button>
            <button class="btn btn-warning" onclick="sendKey('ctrl+c')">Ctrl+C</button>
            <button class="btn btn-warning" onclick="sendKey('ctrl+v')">Ctrl+V</button>
        </div>
        
        <div id="feedback" class="feedback"></div>
    </div>

    <script>
        // Force polling for corporate networks (change to true if WebSocket blocked)
        const FORCE_POLLING = false;
        
        const transportOptions = FORCE_POLLING 
            ? ['polling'] 
            : ['websocket', 'polling'];  // Try WebSocket first, fallback to polling
        
        const socket = io('/', {
            transports: transportOptions,
            upgrade: !FORCE_POLLING,
            reconnection: true,
            reconnectionAttempts: Infinity,
            timeout: 20000
        });
        
        const statusEl = document.getElementById('status');
        const transportEl = document.getElementById('transport');
        const textboxEl = document.getElementById('textbox');
        const feedbackEl = document.getElementById('feedback');
        
        function showFeedback(msg, type = 'success') {
            feedbackEl.textContent = msg;
            feedbackEl.className = 'feedback show ' + type;
            setTimeout(() => feedbackEl.classList.remove('show'), 3000);
        }
        
        socket.on('connect', () => {
            statusEl.textContent = 'CONNECTED';
            statusEl.className = 'status connected';
            transportEl.textContent = socket.io.engine.transport.name.toUpperCase();
            showFeedback('Connected to local server!', 'success');
        });
        
        socket.on('disconnect', () => {
            statusEl.textContent = 'DISCONNECTED';
            statusEl.className = 'status disconnected';
            transportEl.textContent = 'Not connected';
        });
        
        socket.on('command_result', (data) => {
            showFeedback(data.message, data.success ? 'success' : 'error');
        });
        
        function sendText() {
            const text = textboxEl.value.trim();
            if (!text) {
                showFeedback('Please enter text', 'error');
                return;
            }
            socket.emit('execute_command', {
                command: 'type',
                data: { text: text }
            });
            textboxEl.value = '';
            textboxEl.focus();
        }
        
        function sendKey(key) {
            socket.emit('execute_command', {
                command: 'key',
                data: { key: key }
            });
        }
        
        textboxEl.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendText();
            }
        });
    </script>
</body>
</html>"""
    return html

@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'version': 'local-1.0',
        'clients': len(connected_clients),
        'timestamp': datetime.now().isoformat()
    })

@socketio.on('connect')
def handle_connect():
    connected_clients.append(request.sid)
    logger.info(f"Client connected: {request.sid} | Total: {len(connected_clients)}")
    emit('connection_confirmed', {'status': 'connected', 'client_id': request.sid})

@socketio.on('disconnect')
def handle_disconnect():
    if request.sid in connected_clients:
        connected_clients.remove(request.sid)
        logger.info(f"Client disconnected: {request.sid} | Remaining: {len(connected_clients)}")

@socketio.on('execute_command')
def handle_execute_command(data):
    try:
        command = data.get('command')
        cmd_data = data.get('data', {})
        
        if command == 'type':
            text = cmd_data.get('text', '')
            if text:
                pyautogui.write(text, interval=0.02)
                emit('command_result', {'success': True, 'message': f'Typed: {text[:50]}...'})
                logger.info(f"Typed text: {text[:50]}...")
        
        elif command == 'key':
            key = cmd_data.get('key', '')
            if key:
                pyautogui.press(key)
                emit('command_result', {'success': True, 'message': f'Key pressed: {key}'})
                logger.info(f"Key pressed: {key}")
        
        elif command == 'click':
            x = cmd_data.get('x', 0)
            y = cmd_data.get('y', 0)
            pyautogui.click(x, y)
            emit('command_result', {'success': True, 'message': f'Clicked at ({x}, {y})'})
            logger.info(f"Clicked at: ({x}, {y})")
            
    except Exception as e:
        logger.error(f"Command error: {e}")
        emit('command_result', {'success': False, 'message': f'Error: {str(e)}'})

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Local Remote Desktop Server')
    parser.add_argument('--port', type=int, default=8090, help='Port to run on (default: 8090)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()
    
    print("=" * 60)
    print("LOCAL REMOTE DESKTOP SERVER")
    print("=" * 60)
    print(f"Starting on port {args.port}...")
    print()
    print("To access from external network:")
    print("1. Install ngrok: https://ngrok.com/download")
    print(f"2. Run: ngrok http {args.port}")
    print("3. Use the ngrok URL from your phone/tablet")
    print()
    print("For corporate networks:")
    print("- WebSocket will fallback to HTTP polling automatically")
    print("- Or set FORCE_POLLING = true in the HTML")
    print("=" * 60)
    print()
    
    socketio.run(app, host='0.0.0.0', port=args.port, debug=args.debug)