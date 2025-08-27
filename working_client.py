#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Working Remote Desktop Client
Based on successful connection test
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
pyautogui.PAUSE = 0.1

class WorkingRemoteClient:
    def __init__(self, server_url='https://remote-desktop-ycqe3vmjva-uc.a.run.app'):
        self.sio = socketio.Client(reconnection=True, reconnection_delay=2)
        self.server_url = server_url
        self.connected = False
        self.setup_events()
        self.start_periodic_screenshot()

    def setup_events(self):
        @self.sio.event
        def connect():
            print('[CONNECTED] Connected to Cloud Run server')
            print(f'[SERVER] {self.server_url}')
            print('[REGISTER] Registering as PC client...')
            self.connected = True
            self.sio.emit('register_local_client')
            
            # Send immediate screenshot after connection
            time.sleep(1)  # Wait for registration
            self.send_screenshot()
            print('[AUTO_SCREENSHOT] Initial screenshot sent')

        @self.sio.event
        def disconnect():
            print('[DISCONNECTED] Disconnected from server')
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
                        # Auto-focus before typing
                        self.auto_focus_claude_bottom_right()
                        time.sleep(0.5)  # Wait for focus
                        
                        pyautogui.typewrite(text)
                        print(f'[TYPE] OK: {text[:20]}... (with auto-focus)')
                        self.sio.emit('command_result', {'command': 'TYPE', 'success': True})

                elif command == 'key':
                    key = cmd_data.get('key', '')
                    if key:
                        # Auto-focus for Enter key
                        if key.lower() == 'enter':
                            self.auto_focus_claude_bottom_right()
                            time.sleep(0.3)
                        
                        pyautogui.press(key)
                        print(f'[KEY] OK: {key} (with auto-focus)')
                        self.sio.emit('command_result', {'command': 'KEY', 'success': True})

                elif command == 'claude_focus_position':
                    position = cmd_data.get('position', 'center')
                    screen_width, screen_height = pyautogui.size()
                    
                    position_coords = {
                        'top-left': (int(screen_width * 0.25), int(screen_height * 0.25)),
                        'top-right': (int(screen_width * 0.75), int(screen_width * 0.25)),
                        'bottom-left': (int(screen_width * 0.25), int(screen_height * 0.75)),
                        'bottom-right': (int(screen_width * 0.75), int(screen_height * 0.90)),
                        'center': (int(screen_width * 0.5), int(screen_height * 0.5))
                    }
                    
                    if position in position_coords:
                        x, y = position_coords[position]
                        pyautogui.click(x, y)
                        time.sleep(0.3)
                        print(f'[CLAUDE_FOCUS] {position} clicked at ({x}, {y})')
                        self.sio.emit('command_result', {'command': f'CLAUDE_FOCUS_{position.upper()}', 'success': True})

                elif command == 'click':
                    x = cmd_data.get('x', 0)
                    y = cmd_data.get('y', 0)
                    if x and y:
                        pyautogui.click(x, y)
                        print(f'[CLICK] OK: ({x}, {y})')
                        self.sio.emit('command_result', {'command': 'CLICK', 'success': True})

                elif command == 'screenshot':
                    self.send_screenshot()

            except Exception as e:
                print(f'[ERROR] Command failed: {e}')
                self.sio.emit('command_result', {'command': command.upper(), 'success': False})

        @self.sio.event
        def screenshot_request():
            print('[SCREENSHOT] Screenshot requested')
            self.send_screenshot()

        @self.sio.event
        def web_client_connected():
            print('[WEB_RELOAD] Web client connected/reloaded')
            # Send fresh screenshot when web client connects
            time.sleep(0.5)
            self.send_screenshot()
            print('[AUTO_SCREENSHOT] Screenshot sent for web reload')

        @self.sio.event
        def connect_error(data):
            print(f'[CONNECTION_ERROR] {data}')

    def send_screenshot(self):
        try:
            screenshot = pyautogui.screenshot()
            
            # Resize for performance
            screenshot = screenshot.resize((800, 600))
            
            # Convert to base64
            buffer = io.BytesIO()
            screenshot.save(buffer, format='JPEG', quality=75)
            img_data = base64.b64encode(buffer.getvalue()).decode()
            
            self.sio.emit('screen_update', {'image': img_data})
            print('[SCREENSHOT] Sent successfully')
            
        except Exception as e:
            print(f'[SCREENSHOT_ERROR] {e}')

    def start_periodic_screenshot(self):
        def periodic_sender():
            while True:
                time.sleep(10)  # Every 10 seconds
                if self.connected:
                    try:
                        self.send_screenshot()
                        # Remove frequent logging
                    except:
                        pass
        
        thread = threading.Thread(target=periodic_sender, daemon=True)
        thread.start()

    def auto_focus_claude_bottom_right(self):
        """Automatically focus on Claude Code bottom-right window"""
        try:
            screen_width, screen_height = pyautogui.size()
            # Bottom-right position optimized for Claude Code chat input
            x = int(screen_width * 0.75)
            y = int(screen_height * 0.90)
            
            # Click to focus
            pyautogui.click(x, y)
            time.sleep(0.1)
            
            # Ensure chat input is focused with Ctrl+End
            pyautogui.press('ctrl+end')
            
            print(f'[AUTO_FOCUS] Claude Code bottom-right focused at ({x}, {y})')
            
        except Exception as e:
            print(f'[AUTO_FOCUS_ERROR] {e}')

    def connect(self):
        try:
            print("[INIT] Starting Working Remote Desktop Client")
            print(f"[CONNECTING] {self.server_url}...")
            
            # Use polling transport for reliability
            self.sio.connect(self.server_url, transports=['polling'], wait_timeout=10)
            
            print("[SUCCESS] Connected! Client is running...")
            print("[INSTRUCTIONS] Open web interface on smartphone")
            print(f"[URL] {self.server_url}")
            print("[STATUS] Waiting for commands...")
            
            # Keep connection alive
            self.sio.wait()
            
        except KeyboardInterrupt:
            print('\n[STOP] Stopping client...')
            self.sio.disconnect()
        except Exception as e:
            print(f'[CONNECTION_FAILED] {e}')
            print('[SOLUTIONS]')
            print('  1. Check internet connection')
            print('  2. Verify Cloud Run service is running')
            print('  3. Try again in a few seconds')
            return False
        return True

if __name__ == '__main__':
    print("=" * 60)
    print("  Working Remote Desktop Client")
    print("=" * 60)
    
    client = WorkingRemoteClient()
    success = client.connect()
    
    if not success:
        print("[FAILED] Connection failed!")
        sys.exit(1)