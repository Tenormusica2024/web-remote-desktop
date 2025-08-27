#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Remote Desktop Client for Cloud Run
Connects to Cloud Run server and executes commands locally
"""

import socketio
import pyautogui
import sys
import time
import argparse
import logging

# Security settings
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RemoteClient:
    def __init__(self, server_url):
        self.sio = socketio.Client()
        self.server_url = server_url
        self.setup_events()

    def setup_events(self):
        @self.sio.event
        def connect():
            print('Connected to Cloud Run server')
            print(f'Server URL: {self.server_url}')
            self.sio.emit('register_local_client')

        @self.sio.event
        def disconnect():
            print('Disconnected from server')

        @self.sio.event
        def execute_command(data):
            try:
                command = data.get('command')
                cmd_data = data.get('data', {})
                
                print(f'Executing command: {command} with data: {cmd_data}')

                if command == 'type':
                    text = cmd_data.get('text', '')
                    if text:
                        pyautogui.write(text, interval=0.02)
                        self.sio.emit('command_result', {'command': 'TYPE', 'success': True})
                        print(f'Typed: {text}')

                elif command == 'key':
                    key = cmd_data.get('key', '')
                    if key:
                        pyautogui.press(key)
                        self.sio.emit('command_result', {'command': f'KEY({key})', 'success': True})
                        print(f'Key pressed: {key}')

                elif command == 'click':
                    x = cmd_data.get('x', 0)
                    y = cmd_data.get('y', 0)
                    pyautogui.click(x, y)
                    self.sio.emit('command_result', {'command': f'CLICK({x},{y})', 'success': True})
                    print(f'Clicked: {x}, {y}')

            except Exception as e:
                print(f'Command error: {e}')
                self.sio.emit('command_result', {'command': command.upper(), 'success': False})

        @self.sio.event
        def registration_success(data):
            print(f'Registration successful: {data}')

    def connect(self):
        try:
            print(f'Connecting to {self.server_url}...')
            self.sio.connect(self.server_url, transports=['websocket', 'polling'])
            print('Connected! Waiting for commands...')
            print('To test: Open the web interface and turn on Remote Mode')
            self.sio.wait()
        except Exception as e:
            print(f'Connection error: {e}')
            return False

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Remote Desktop Client for Cloud Run')
    parser.add_argument('server_url', nargs='?', 
                       default='https://remote-desktop-ycqe3vmjva-uc.a.run.app',
                       help='Cloud Run server URL')
    args = parser.parse_args()

    print("=============================================================")
    print("  Remote Desktop Client - Cloud Run Edition")
    print("=============================================================")
    print(f"Server URL: {args.server_url}")
    print("Starting connection...")
    print()

    client = RemoteClient(args.server_url)
    success = client.connect()
    
    if not success:
        print("Connection failed!")
        sys.exit(1)