#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Connect Remote Desktop Client
Optimized for fast connection and reliable text sending
"""

import socketio
import pyautogui
import base64
import io
import sys
import time

# Security settings
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05  # Faster response

class QuickRemoteClient:
    def __init__(self, server_url='https://remote-desktop-ycqe3vmjva-uc.a.run.app'):
        # Simple, fast connection
        self.sio = socketio.Client(logger=False, engineio_logger=False)
        self.server_url = server_url
        self.setup_events()

    def setup_events(self):
        @self.sio.event
        def connect():
            print('[CONNECTED] Quick client connected!')
            self.sio.emit('register_local_client')
            # Send screenshot immediately
            self.send_screenshot()
            print('[READY] Client ready for commands')

        @self.sio.event
        def disconnect():
            print('[DISCONNECTED] Client disconnected')

        @self.sio.event
        def execute_command(data):
            command = data.get('command')
            cmd_data = data.get('data', {})
            
            print(f'[EXEC] {command}: {cmd_data}')

            if command == 'type':
                text = cmd_data.get('text', '')
                if text:
                    # Direct focus and type
                    self.focus_claude_chat()
                    pyautogui.typewrite(text, interval=0.02)
                    print(f'[TYPE] Sent: {text}')
                    self.sio.emit('command_result', {'command': 'TYPE', 'success': True})

            elif command == 'key':
                key = cmd_data.get('key', '')
                if key:
                    # Focus before Enter
                    if key.lower() == 'enter':
                        self.focus_claude_chat()
                    pyautogui.press(key)
                    print(f'[KEY] Pressed: {key}')
                    self.sio.emit('command_result', {'command': 'KEY', 'success': True})

            elif command == 'claude_focus_position':
                position = cmd_data.get('position', 'bottom-right')
                self.focus_claude_position(position)

            elif command == 'screenshot':
                self.send_screenshot()

        @self.sio.event
        def screenshot_request():
            self.send_screenshot()

        @self.sio.event
        def web_client_connected():
            print('[WEB] Web client connected - sending fresh screenshot')
            self.send_screenshot()

    def focus_claude_chat(self):
        """Fast focus on Claude Code chat input"""
        screen_width, screen_height = pyautogui.size()
        # Bottom-right Claude Code position
        x = int(screen_width * 0.75)
        y = int(screen_height * 0.90)
        
        pyautogui.click(x, y)
        time.sleep(0.1)
        print(f'[FOCUS] Claude chat focused at ({x}, {y})')

    def focus_claude_position(self, position):
        """Focus on specific Claude Code window position"""
        screen_width, screen_height = pyautogui.size()
        
        positions = {
            'top-left': (int(screen_width * 0.25), int(screen_height * 0.25)),
            'top-right': (int(screen_width * 0.75), int(screen_height * 0.25)),
            'bottom-left': (int(screen_width * 0.25), int(screen_height * 0.75)),
            'bottom-right': (int(screen_width * 0.75), int(screen_height * 0.90)),
            'center': (int(screen_width * 0.5), int(screen_height * 0.5))
        }
        
        if position in positions:
            x, y = positions[position]
            pyautogui.click(x, y)
            print(f'[FOCUS] {position} clicked at ({x}, {y})')
            self.sio.emit('command_result', {'command': f'FOCUS_{position.upper()}', 'success': True})

    def send_screenshot(self):
        try:
            screenshot = pyautogui.screenshot()
            screenshot = screenshot.resize((800, 600))  # Fast resize
            
            buffer = io.BytesIO()
            screenshot.save(buffer, format='JPEG', quality=70)
            img_data = base64.b64encode(buffer.getvalue()).decode()
            
            self.sio.emit('screen_update', {'image': img_data})
            print('[SCREENSHOT] Sent')
        except Exception as e:
            print(f'[SCREENSHOT_ERROR] {e}')

    def connect(self):
        try:
            print("[QUICK CLIENT] Starting...")
            print(f"[CONNECTING] {self.server_url}")
            
            # Fast connection with polling only
            self.sio.connect(self.server_url, transports=['polling'], wait_timeout=5)
            
            print("[ONLINE] Connected and ready!")
            print(f"[URL] {self.server_url}")
            
            # Keep alive
            self.sio.wait()
            
        except KeyboardInterrupt:
            print('\n[STOP] Stopping...')
            self.sio.disconnect()
        except Exception as e:
            print(f'[ERROR] Connection failed: {e}')
            return False
        return True

if __name__ == '__main__':
    print("=" * 50)
    print("  Quick Remote Desktop Client")
    print("=" * 50)
    
    client = QuickRemoteClient()
    client.connect()