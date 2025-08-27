#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最小限サーバー - 映るまでの復旧専用ライン
HTTP fallback first, Socket.IO second
"""
import os
import base64
from datetime import datetime
from flask import Flask, Response, request, jsonify
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'minimal-recovery-2025'

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True,
    async_mode='threading'
)

# 最小グローバル状態
latest_jpeg = None  # JPEG bytes
clients = []
local_clients = []

@app.route('/')
def index():
    return '''<!DOCTYPE html>
<html>
<head>
    <title>Remote Desktop</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        body { background: #111; color: white; margin: 0; font-family: Arial, sans-serif; }
        .container { text-align: center; padding: 10px; }
        .screen { 
            border: 2px solid #4CAF50; 
            margin: 10px auto; 
            max-width: 95vw; 
            max-height: 80vh; 
            width: auto; 
            height: auto;
            object-fit: contain;
        }
        .status { background: #333; padding: 10px; }
        .controls { margin: 10px 0; }
        .controls button { 
            margin: 5px; 
            padding: 10px 20px; 
            background: #4CAF50; 
            color: white; 
            border: none; 
            border-radius: 5px; 
            cursor: pointer; 
            font-size: 16px;
        }
        .controls button:hover { background: #45a049; }
        #status { 
            margin-top: 10px; 
            padding: 5px; 
            font-size: 14px; 
            color: #4CAF50; 
        }
    </style>
</head>
<body>
    <div class="status">
        <h2>Remote Desktop Server</h2>
        <p>Status: Running</p>
    </div>
    <div class="container">
        <h3>📺 PC Screen Display</h3>
        <img id="screen" class="screen" src="/frame.jpg" alt="PC Screen" style="max-width: 90%; height: auto;">
        <div class="controls">
            <button onclick="refresh()">🔄 Refresh</button>
            <button onclick="auto()">▶️ Auto (2秒間隔)</button>
            <button onclick="stop()">⏹️ Stop</button>
        </div>
        <div id="status"></div>
        
        <!-- テキスト貼り付け機能 -->
        <div class="paste-section" style="max-width:800px;margin:20px auto;text-align:left;padding:15px;background:#222;border-radius:10px;">
            <h3>📝 Paste to Claude Code</h3>
            <textarea id="msg" rows="4" placeholder="テキストを入力してPCのClaude Codeに貼り付け..." style="width:100%;font-size:14px;padding:8px;border:1px solid #555;border-radius:5px;background:#333;color:white;resize:vertical;"></textarea>
            
            <div style="margin-top:10px;display:flex;gap:15px;align-items:center;flex-wrap:wrap;">
                <!-- 貼り付け先選択 -->
                <div style="display:flex;gap:10px;align-items:center;">
                    <label style="font-size:14px;">貼り付け先:</label>
                    <label style="font-size:14px;"><input type="radio" name="target" value="chat" checked> 💬 チャット欄（右下）</label>
                    <label style="font-size:14px;"><input type="radio" name="target" value="comment"> 💭 コメント欄（右上）</label>
                </div>
            </div>
            
            <div style="margin-top:10px;display:flex;gap:10px;align-items:center;flex-wrap:wrap;">
                <label style="font-size:14px;">
                    <input id="autoEnter" type="checkbox" checked> 送信時に Enter を自動押下
                </label>
                <button onclick="sendPaste()" style="background:#4CAF50;color:white;border:none;padding:8px 15px;border-radius:5px;cursor:pointer;">
                    📤 貼り付け送信 (Ctrl+Enter)
                </button>
                <button onclick="sendHTTP()" style="background:#2196F3;color:white;border:none;padding:8px 15px;border-radius:5px;cursor:pointer;">
                    🌐 HTTP Fallback
                </button>
                <span id="pasteStatus" style="color:#4CAF50;margin-left:10px;font-size:14px;"></span>
            </div>
        </div>
    </div>
    <script>
        let autoRefresh = null;
        const socket = io();
        
        function refresh() {
            const img = document.getElementById('screen');
            img.src = '/frame.jpg?' + Date.now();
            document.getElementById('status').textContent = 'Refreshed at ' + new Date().toLocaleTimeString();
        }
        function auto() {
            if (autoRefresh) clearInterval(autoRefresh);
            autoRefresh = setInterval(refresh, 2000);
            document.getElementById('status').textContent = '▶️ Auto refresh every 2s';
        }
        function stop() {
            if (autoRefresh) {
                clearInterval(autoRefresh);
                autoRefresh = null;
            }
            document.getElementById('status').textContent = '⏹️ Auto refresh stopped';
        }
        
        // テキスト貼り付け機能
        function flashStatus(text) {
            const status = document.getElementById('pasteStatus');
            status.textContent = text;
            setTimeout(() => status.textContent = '', 2000);
        }
        
        function getTarget() {
            const radios = document.getElementsByName('target');
            for (let radio of radios) {
                if (radio.checked) return radio.value;
            }
            return 'chat'; // デフォルト
        }
        
        async function sendHTTP() {
            const text = document.getElementById('msg').value.trim();
            const autoEnter = document.getElementById('autoEnter').checked;
            const target = getTarget();
            if (!text) {
                flashStatus('❌ テキストを入力してください');
                return;
            }
            try {
                const response = await fetch('/paste', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                    body: new URLSearchParams({text, autoEnter: autoEnter ? '1' : '0', target})
                });
                flashStatus(response.ok ? '✅ HTTP送信完了' : '❌ HTTP送信失敗');
            } catch(e) {
                flashStatus('❌ HTTP送信エラー');
            }
        }
        
        function sendPaste() {
            const text = document.getElementById('msg').value.trim();
            const autoEnter = document.getElementById('autoEnter').checked;
            const target = getTarget();
            const targetText = target === 'comment' ? 'コメント欄' : 'チャット欄';
            if (!text) {
                flashStatus('❌ テキストを入力してください');
                return;
            }
            if (socket.connected) {
                socket.emit('paste_text', {text, send_enter: autoEnter, target});
                flashStatus(`✅ ${targetText}に送信完了`);
            } else {
                sendHTTP();
            }
        }
        
        // Ctrl+Enter でテキスト送信
        document.getElementById('msg').addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'Enter') {
                e.preventDefault();
                sendPaste();
            }
        });
        
        socket.on('connect', () => console.log('Socket connected'));
        socket.on('disconnect', () => console.log('Socket disconnected'));
    </script>
</body>
</html>'''

@app.get("/health")
def health():
    return {
        'status': 'minimal-server',
        'clients': len(clients),
        'local_clients': len(local_clients),
        'has_jpeg': latest_jpeg is not None,
        'jpeg_size': len(latest_jpeg) if latest_jpeg else 0,
        'timestamp': datetime.now().isoformat()
    }

@app.get("/frame.jpg")
def frame():
    """HTTP fallback - JPEG直返し"""
    global latest_jpeg
    if latest_jpeg:
        return Response(latest_jpeg, mimetype="image/jpeg")
    return ("", 204)

@socketio.on('connect')
def on_connect():
    clients.append(request.sid)
    print(f"Client connected: {request.sid} (Total: {len(clients)})")

@socketio.on('disconnect') 
def on_disconnect():
    if request.sid in clients:
        clients.remove(request.sid)
    if request.sid in local_clients:
        local_clients.remove(request.sid)
        print(f"Local client disconnected: {request.sid}")

@socketio.on('register_local_client')
def register_local():
    if request.sid not in local_clients:
        local_clients.append(request.sid)
        print(f"Local client registered: {request.sid}")

@socketio.on('screen_update')
def screen_update(data):
    global latest_jpeg
    b64 = data.get('image')
    if b64:
        try:
            # Base64 → JPEG bytes
            latest_jpeg = base64.b64decode(b64.split(',', 1)[-1] if ',' in b64 else b64)
            print(f"Screen updated: {len(latest_jpeg)} bytes")
        except Exception as e:
            print(f"Base64 decode error: {e}")

@socketio.on('paste_text')
def on_paste_text(data):
    """テキスト貼り付け指示をローカルPCクライアントにブロードキャスト"""
    text = (data or {}).get('text', '').strip()
    send_enter = bool((data or {}).get('send_enter', False))
    target = (data or {}).get('target', 'chat')  # chat or comment
    if text:
        print(f"Paste text requested: {len(text)} chars, enter={send_enter}, target={target}")
        emit('paste_text', {'text': text, 'send_enter': send_enter, 'target': target}, broadcast=True)

@app.post('/paste')
def http_paste():
    """HTTPフォールバック: /paste にPOSTでテキスト送信"""
    text = request.form.get('text', '').strip()
    auto_enter = request.form.get('autoEnter', '0') in ('1', 'true', 'True', 'on')
    target = request.form.get('target', 'chat')
    if not text:
        return jsonify({'ok': False, 'error': 'empty text'}), 400
    
    print(f"HTTP paste: {len(text)} chars, enter={auto_enter}, target={target}")
    socketio.emit('paste_text', {'text': text, 'send_enter': auto_enter, 'target': target}, broadcast=True)
    return jsonify({'ok': True})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"最小限サーバー起動 - Port {port}")
    socketio.run(app, host='0.0.0.0', port=port, debug=False)