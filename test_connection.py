#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple connection test
"""

import socketio
import time

def test_connection():
    print("Testing connection to Cloud Run service...")
    
    # Test basic HTTP first
    import urllib.request
    import urllib.error
    
    url = "https://remote-desktop-ycqe3vmjva-uc.a.run.app"
    
    try:
        print(f"Testing HTTP connection to {url}")
        response = urllib.request.urlopen(url)
        print(f"HTTP Status: {response.getcode()}")
        print("[OK] HTTP connection successful")
        
        # Now test Socket.IO
        print("\nTesting Socket.IO connection...")
        sio = socketio.Client(logger=False, engineio_logger=False)
        
        @sio.event
        def connect():
            print("[OK] Socket.IO connected successfully!")
            sio.disconnect()
        
        @sio.event  
        def connect_error(data):
            print(f"[ERROR] Socket.IO connection error: {data}")
        
        @sio.event
        def disconnect():
            print("Socket.IO disconnected")
            
        # Try connection with polling first
        sio.connect(url, transports=['polling'], wait_timeout=5)
        time.sleep(2)
        
    except urllib.error.URLError as e:
        print(f"[ERROR] HTTP connection failed: {e}")
    except Exception as e:
        print(f"[ERROR] Connection test failed: {e}")
    
    print("\nConnection test complete.")

if __name__ == '__main__':
    test_connection()