#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple connection test
"""
import socketio
import time

print("TESTING CONNECTION...")

sio = socketio.Client()
server_url = 'https://remote-desktop-ycqe3vmjva-uc.a.run.app'

@sio.event
def connect():
    print("CONNECTION SUCCESS!")
    sio.emit('register_local_client')
    print("REGISTERED AS LOCAL CLIENT")
    
    time.sleep(2)
    sio.disconnect()
    print("TEST COMPLETE")

@sio.event
def connect_error(data):
    print(f"CONNECTION ERROR: {data}")

@sio.event
def disconnect():
    print("DISCONNECTED CLEANLY")

try:
    print(f"CONNECTING TO: {server_url}")
    sio.connect(server_url, transports=['polling'], wait_timeout=10)
    print("CONNECTION ESTABLISHED")
except Exception as e:
    print(f"CONNECTION FAILED: {e}")