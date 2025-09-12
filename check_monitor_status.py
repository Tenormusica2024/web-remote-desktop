#!/usr/bin/env python3
"""
Check if the monitoring system is running and show recent activity
"""

import os
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

ROOT = Path(__file__).resolve().parent
LOG_FILE = ROOT / "monitor.log"

def check_process_status():
    """監視プロセスが動作中かチェック"""
    try:
        # Windowsでpython.exeプロセスを確認
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], 
                              capture_output=True, text=True, shell=True)
        
        if 'python.exe' in result.stdout:
            print("Python processes are running")
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if 'python.exe' in line:
                    print(f"   {line}")
            return True
        else:
            print("No python.exe processes found")
            return False
            
    except Exception as e:
        print(f"Error checking processes: {e}")
        return False

def check_recent_activity():
    """最近のログ活動をチェック"""
    try:
        if not LOG_FILE.exists():
            print("No log file found")
            return
            
        # 最新の10行を読み取り
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        if not lines:
            print("Log file is empty")
            return
            
        print(f"\nRecent activity (last 5 entries):")
        print("-" * 60)
        
        recent_lines = lines[-5:] if len(lines) >= 5 else lines
        for line in recent_lines:
            print(f"   {line.strip()}")
        
        # 最後のエントリの時刻をチェック
        last_line = lines[-1].strip()
        if '[' in last_line and ']' in last_line:
            try:
                # ログの時刻部分を抽出
                time_str = last_line.split('[')[1].split(']')[0]
                log_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                current_time = datetime.now()
                time_diff = current_time - log_time
                
                if time_diff < timedelta(minutes=5):
                    print(f"\nSystem is active (last activity: {time_diff.seconds//60} minutes ago)")
                else:
                    print(f"\nSystem may be idle (last activity: {time_diff} ago)")
                    
            except Exception as e:
                print(f"\nCould not parse log timestamp: {e}")
        
    except Exception as e:
        print(f"Error reading log: {e}")

def main():
    print("=== GitHub Remote Desktop Monitor Status ===")
    print(f"Directory: {ROOT}")
    print(f"Log file: {LOG_FILE}")
    print()
    
    # プロセス状況確認
    process_running = check_process_status()
    
    # ログ活動確認
    check_recent_activity()
    
    print("\n" + "="*50)
    if process_running:
        print("Monitor appears to be running")
        print("Use 'stop_monitor.bat' to stop")
    else:
        print("Monitor is not running")
        print("Use 'start_monitor.bat' to start")

if __name__ == "__main__":
    main()