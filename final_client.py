#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Final Remote Desktop Client - Bulletproof text sending
"""

import socketio
import pyautogui
import base64
import io
import sys
import time
import threading

# Security settings
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05

class FinalRemoteClient:
    def __init__(self, server_url='https://remote-desktop-ycqe3vmjva-uc.a.run.app'):
        self.sio = socketio.Client(reconnection=True, reconnection_delay=2)
        self.server_url = server_url
        self.connected = False
        self.setup_events()
        self.start_periodic_screenshot()

    def setup_events(self):
        @self.sio.event
        def connect():
            print('[CONNECTED] Final client connected!')
            self.connected = True
            self.sio.emit('register_local_client')
            
            # Send immediate screenshot
            time.sleep(1)
            self.send_screenshot()
            print('[READY] Client ready for commands')

        @self.sio.event
        def disconnect():
            print('[DISCONNECTED] Client disconnected')
            self.connected = False

        @self.sio.event
        def execute_command(data):
            try:
                command = data.get('command')
                cmd_data = data.get('data', {})
                print(f'[COMMAND] {command}: {cmd_data}')

                if command == 'type':
                    text = cmd_data.get('text', '')
                    if text:
                        success = self.safe_type_text(text)
                        self.sio.emit('command_result', {'command': 'TYPE', 'success': success})

                elif command == 'key':
                    key = cmd_data.get('key', '')
                    if key:
                        success = self.safe_press_key(key)
                        self.sio.emit('command_result', {'command': 'KEY', 'success': success})

                elif command == 'claude_focus_position':
                    position = cmd_data.get('position', 'bottom-right')
                    success = self.focus_claude_position(position)
                    self.sio.emit('command_result', {'command': f'FOCUS_{position.upper()}', 'success': success})

                elif command == 'screenshot':
                    self.send_screenshot()

            except Exception as e:
                print(f'[ERROR] Command failed: {e}')
                self.sio.emit('command_result', {'command': command.upper(), 'success': False})

        @self.sio.event
        def screenshot_request():
            self.send_screenshot()

        @self.sio.event
        def web_client_connected():
            print('[WEB_RELOAD] Web client reconnected')
            time.sleep(0.5)
            self.send_screenshot()

    def safe_type_text(self, text):
        """Bulletproof text typing with multiple fallbacks"""
        try:
            print(f'[TYPE_START] Typing: {text}')
            
            # Step 1: Triple focus attempt
            for attempt in range(3):
                self.focus_claude_chat()
                time.sleep(0.2)
            
            # Step 2: Clear any existing text
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.1)
            
            # Step 3: Type text slowly for reliability
            pyautogui.typewrite(text, interval=0.03)
            
            print(f'[TYPE_SUCCESS] Text typed: {text}')
            return True
            
        except Exception as e:
            print(f'[TYPE_ERROR] {e}')
            return False

    def safe_press_key(self, key):
        """Bulletproof key pressing"""
        try:
            print(f'[KEY_START] Pressing: {key}')
            
            # Focus before Enter key
            if key.lower() == 'enter':
                self.focus_claude_chat()
                time.sleep(0.2)
            
            pyautogui.press(key)
            print(f'[KEY_SUCCESS] Key pressed: {key}')
            return True
            
        except Exception as e:
            print(f'[KEY_ERROR] {e}')
            return False

    def focus_claude_chat(self):
        """Ultra-reliable Claude Code chat focus"""
        try:
            screen_width, screen_height = pyautogui.size()
            
            # Multiple focus attempts at different positions
            positions = [
                (int(screen_width * 0.75), int(screen_height * 0.90)),  # Bottom-right
                (int(screen_width * 0.75), int(screen_height * 0.88)),  # Slightly higher
                (int(screen_width * 0.73), int(screen_height * 0.92)),  # Slightly left/down
            ]
            
            for x, y in positions:
                pyautogui.click(x, y)
                time.sleep(0.05)
            
            # Ensure cursor is at the end
            pyautogui.press('end')
            time.sleep(0.05)
            
            print(f'[FOCUS_SUCCESS] Claude chat focused')
            
        except Exception as e:
            print(f'[FOCUS_ERROR] {e}')

    def focus_claude_position(self, position):
        """Focus on specific Claude Code window"""
        try:
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
                time.sleep(0.1)
                print(f'[FOCUS_POSITION] {position} clicked at ({x}, {y})')
                return True
            return False
            
        except Exception as e:
            print(f'[FOCUS_POSITION_ERROR] {e}')
            return False

    def send_screenshot(self):
        try:
            screenshot = pyautogui.screenshot()
            screenshot = screenshot.resize((800, 600))
            
            buffer = io.BytesIO()
            screenshot.save(buffer, format='JPEG', quality=70)
            img_data = base64.b64encode(buffer.getvalue()).decode()
            
            self.sio.emit('screen_update', {'image': img_data})
            
        except Exception as e:
            print(f'[SCREENSHOT_ERROR] {e}')

    def start_periodic_screenshot(self):
        def periodic_sender():
            while True:
                time.sleep(8)  # Every 8 seconds
                if self.connected:
                    try:
                        self.send_screenshot()
                    except:
                        pass
        
        thread = threading.Thread(target=periodic_sender, daemon=True)
        thread.start()

    def connect(self):
        try:
            print("[FINAL CLIENT] Starting bulletproof remote desktop client")
            print(f"[CONNECTING] {self.server_url}")
            
            self.sio.connect(self.server_url, transports=['polling'], wait_timeout=10)
            
            print("[SUCCESS] Connected and operational!")
            print(f"[URL] {self.server_url}")
            print("[STATUS] Ready for text input commands")
            
            self.sio.wait()
            
        except KeyboardInterrupt:
            print('\n[STOP] Stopping client...')
            self.sio.disconnect()
        except Exception as e:
            print(f'[CONNECTION_ERROR] {e}')
            return False
        return True

if __name__ == '__main__':
    print("=" * 60)
    print("  Final Remote Desktop Client - Bulletproof Text Sending")
    print("=" * 60)
    
    client = FinalRemoteClient()
    client.connect()