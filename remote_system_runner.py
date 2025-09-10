#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Remote system runner - run the system from remote environment
"""
import os
import subprocess
import sys
import time
from pathlib import Path

def setup_environment():
    """Set up environment variables"""
    env_vars = {
        'GH_REPO': 'Tenormusica2024/web-remote-desktop',
        'GH_ISSUE': '3',
        'GH_TOKEN': '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',
        'POLL_SEC': '5',
        'DEFAULT_PANE': 'lower', 
        'ONLY_AUTHOR': 'Tenormusica2024'
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
    
    print("Environment variables set")

def run_system_limited():
    """Run system for a limited time"""
    print("=== Remote System Execution ===")
    setup_environment()
    
    # Check if coordinate file exists
    coord_file = Path(".gh_issue_to_claude_coords.json")
    if not coord_file.exists():
        print("Error: Coordinate file not found. Running auto-calibration...")
        subprocess.run([sys.executable, "auto_calibrate.py"], check=True)
    
    print("Starting GitHub Issue to Claude Code system...")
    print("This will run for 30 seconds to process pending comments")
    
    # Run the main system
    try:
        # Use timeout command to limit execution time
        cmd = [sys.executable, "gh_issue_to_claude_paste.py"]
        process = subprocess.Popen(cmd, 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE,
                                 text=True,
                                 encoding='utf-8',
                                 errors='replace')
        
        # Wait for 30 seconds or until process completes
        try:
            stdout, stderr = process.communicate(timeout=30)
            print("System output:")
            print(stdout)
            if stderr:
                print("Errors:")
                print(stderr)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            print("System ran for 30 seconds and was stopped")
            print("Last output:")
            print(stdout[-500:] if stdout else "No output")
            
    except Exception as e:
        print(f"Error running system: {e}")
    
    print("System execution completed")

if __name__ == "__main__":
    run_system_limited()