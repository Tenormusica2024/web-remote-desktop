#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Remote Desktop Client with Screen Sharing
Connects to Cloud Run server and provides screen sharing + remote control
"""

import socketio
import pyautogui
import base64
import io
import sys
import time
import logging
import threading

# Security settings
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedRemoteClient:
    def __init__(self, server_url='https://remote-desktop-ycqe3vmjva-uc.a.run.app'):
        # Enable HTTP polling fallback for corporate networks
        self.sio = socketio.Client(reconnection=True, reconnection_delay=2, 
                                 reconnection_delay_max=5, reconnection_attempts=5,
                                 logger=False, engineio_logger=False)
        self.server_url = server_url
        self.setup_events()

    def setup_events(self):
        @self.sio.event
        def connect():
            print('Connected to Cloud Run server')
            print(f'Server URL: {self.server_url}')
            print('Open the web interface on your smartphone!')
            self.sio.emit('register_local_client')

        @self.sio.event
        def disconnect():
            print('Disconnected from server')

        @self.sio.event
        def execute_command(data):
            try:
                command = data.get('command')
                cmd_data = data.get('data', {})
                print(f'Executing: {command} - {cmd_data}')

                if command == 'type':
                    text = cmd_data.get('text', '')
                    if text:
                        print(f'[DEBUG] Received text to type: "{text}" (length: {len(text)})')
                        try:
                            # Check if text contains any problematic characters
                            print(f'[DEBUG] Text encoding check: {repr(text)}')
                            pyautogui.write(text, interval=0.05)  # Slower typing for reliability
                            print(f'[DEBUG] Successfully typed text')
                            self.sio.emit('command_result', {'command': 'TYPE', 'success': True})
                            print(f'✅ Typed: "{text}"')
                        except Exception as type_error:
                            print(f'❌ Text typing error: {type_error}')
                            self.sio.emit('command_result', {'command': 'TYPE', 'success': False})
                    else:
                        print('[DEBUG] Empty text received - ignoring')
                        self.sio.emit('command_result', {'command': 'TYPE_EMPTY', 'success': False})

                elif command == 'key':
                    key = cmd_data.get('key', '')
                    if key:
                        pyautogui.press(key)
                        self.sio.emit('command_result', {'command': f'KEY({key})', 'success': True})
                        print(f'Key: {key}')

                elif command == 'click':
                    x = cmd_data.get('x', 0)
                    y = cmd_data.get('y', 0)
                    pyautogui.click(x, y)
                    self.sio.emit('command_result', {'command': f'CLICK({x},{y})', 'success': True})
                    print(f'Clicked: {x}, {y}')

                elif command == 'claude_focus_position':
                    # Multi-window Claude Code focus by screen position
                    try:
                        position = cmd_data.get('position', 'center')
                        screen_width, screen_height = pyautogui.size()
                        
                        # Calculate click coordinates based on position
                        position_coords = {
                            'top-left': (int(screen_width * 0.25), int(screen_height * 0.25)),
                            'top-right': (int(screen_width * 0.75), int(screen_height * 0.25)),
                            'bottom-left': (int(screen_width * 0.25), int(screen_height * 0.75)),
                            'bottom-right': (int(screen_width * 0.75), int(screen_height * 0.75)),
                            'center': (int(screen_width * 0.5), int(screen_height * 0.5))
                        }
                        
                        if position in position_coords:
                            click_x, click_y = position_coords[position]
                            
                            # Click on the specified position to focus window
                            pyautogui.click(click_x, click_y)
                            time.sleep(0.3)
                            
                            # Look for chat input area near bottom of that quadrant
                            if position.startswith('top'):
                                chat_y = int(screen_height * 0.48)  # Slightly lower in top half
                            else:
                                chat_y = int(screen_height * 0.95)  # Very bottom for bottom quadrants
                            
                            if position.endswith('left'):
                                chat_x = int(screen_width * 0.25)   # Left side
                            elif position.endswith('right'):
                                chat_x = int(screen_width * 0.75)   # Right side
                            else:
                                chat_x = int(screen_width * 0.5)    # Center
                            
                            # Click on likely chat input area
                            pyautogui.click(chat_x, chat_y)
                            time.sleep(0.2)
                            
                            # Special handling for bottom-right (single precise click)
                            if position == 'bottom-right':
                                # Single click at optimal position for chat input
                                optimal_y = int(screen_height * 0.90)  # 90% down - should be perfect for chat
                                
                                pyautogui.click(chat_x, optimal_y)
                                time.sleep(0.3)
                                
                                print(f'[DEBUG] Bottom-right: single click at ({chat_x}, {optimal_y})')
                            
                            pyautogui.press('ctrl+end')  # Scroll to bottom
                            time.sleep(0.3)
                            
                            self.sio.emit('command_result', {'command': f'CLAUDE_FOCUS_{position.upper()}', 'success': True})
                            print(f'Claude Code {position} focused at ({chat_x}, {chat_y})')
                        else:
                            self.sio.emit('command_result', {'command': 'CLAUDE_FOCUS_POSITION', 'success': False})
                    except Exception as focus_error:
                        print(f'Claude position focus error: {focus_error}')
                        self.sio.emit('command_result', {'command': 'CLAUDE_FOCUS_POSITION', 'success': False})

                elif command == 'claude_focus_active':
                    # Focus on currently active Claude window
                    try:
                        # Try to find Claude Code windows
                        windows = pyautogui.getWindowsWithTitle('Claude')
                        if windows:
                            # Activate the first Claude window found
                            active_window = windows[0]
                            active_window.activate()
                            time.sleep(0.3)
                            
                            # Get window position and size
                            window_left = active_window.left
                            window_top = active_window.top
                            window_width = active_window.width
                            window_height = active_window.height
                            
                            # Click in chat input area (bottom of the active window)
                            chat_x = window_left + (window_width // 2)
                            chat_y = window_top + int(window_height * 0.9)
                            
                            pyautogui.click(chat_x, chat_y)
                            time.sleep(0.2)
                            pyautogui.press('ctrl+end')  # Scroll to bottom
                            time.sleep(0.3)
                            
                            self.sio.emit('command_result', {'command': 'CLAUDE_FOCUS_ACTIVE', 'success': True})
                            print(f'Active Claude Code focused at ({chat_x}, {chat_y})')
                        else:
                            # Fallback: try generic approach
                            pyautogui.press('ctrl+end')
                            time.sleep(0.2)
                            pyautogui.press('tab')
                            self.sio.emit('command_result', {'command': 'CLAUDE_FOCUS_ACTIVE_GENERIC', 'success': True})
                            print('Claude Code focus attempted (no windows found)')
                    except Exception as focus_error:
                        print(f'Claude active focus error: {focus_error}')
                        self.sio.emit('command_result', {'command': 'CLAUDE_FOCUS_ACTIVE', 'success': False})

            except Exception as e:
                print(f'Command error: {e}')
                self.sio.emit('command_result', {'command': command.upper(), 'success': False})

        @self.sio.event
        def request_screenshot():
            try:
                print('Taking screenshot...')
                screenshot = pyautogui.screenshot()
                # Optimize size for mobile viewing
                screenshot.thumbnail((1280, 720), resample=1)
                buffer = io.BytesIO()
                screenshot.save(buffer, format='JPEG', quality=70)
                img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                self.sio.emit('screenshot_data', {'image': img_base64})
                print('Screenshot sent to web client')
            except Exception as e:
                print(f'Screenshot error: {e}')

        @self.sio.event
        def registration_success(data):
            print(f'Registration successful: {data}')

    def connect(self):
        try:
            print(f'Connecting to {self.server_url}...')
            # Try HTTP polling first, then websocket (better for corporate networks)
            self.sio.connect(self.server_url, transports=['polling', 'websocket'], wait_timeout=10)
            print('Connected! Screen sharing active...')
            print()
            print('Instructions:')
            print('   1. Open this URL on your smartphone:')
            print(f'      {self.server_url}')
            print('   2. Wait for "PC client connected"')
            print('   3. Turn ON Remote Mode (OFF → ON)')
            print('   4. You can now see your PC screen and control it!')
            print()
            print('Available controls:')
            print('   - TEXT: Type text into PC')
            print('   - ENTER: Press Enter key')
            print('   - CTRL+C/V: Copy/Paste')
            print('   - CLICK: Tap screen to click')
            print('   - REFRESH: Update screen')
            print()
            print('To stop: Press Ctrl+C')
            print('=' * 60)
            self.sio.wait()
        except KeyboardInterrupt:
            print('\nStopping client...')
            self.sio.disconnect()
        except Exception as e:
            print(f'Connection error: {e}')
            print(f'Server URL: {self.server_url}')
            print('Possible solutions:')
            print('1. Check internet connection')
            print('2. Verify Cloud Run service is running')
            print('3. Try again in a few seconds')
            return False

if __name__ == '__main__':
    print("=" * 60)
    print("  Remote Desktop Client - Enhanced with Screen Sharing")
    print("=" * 60)
    
    client = EnhancedRemoteClient()
    success = client.connect()
    
    if not success:
        print("Connection failed!")
        sys.exit(1)