#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Issue #1 Persistent Comment Monitor Service
Repository: web-remote-desktop
Issue: #1
Runs 24/7 monitoring for upper:/lower: commands only
"""

import time
import logging
import traceback
import sys
from pathlib import Path
from gh_issue1_to_claude_paste import GitHubIssue1CommentMonitor

class PersistentIssue1Service:
    def __init__(self, poll_interval: int = 5):
        """Initialize persistent service"""
        self.poll_interval = poll_interval
        self.monitor = None
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging for persistent service"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f"issue1_persistent_service_{time.strftime('%Y%m%d')}.log"
        
        self.logger = logging.getLogger("Issue1PersistentService")
        self.logger.setLevel(logging.INFO)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # File handler
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def initialize_monitor(self):
        """Initialize comment monitor"""
        try:
            self.monitor = GitHubIssue1CommentMonitor()
            self.logger.info("✅ GitHub Issue #1 Comment Monitor initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize monitor: {e}")
            self.logger.error(traceback.format_exc())
            return False

    def check_for_comments(self):
        """Check for new comments using monitor"""
        try:
            if not self.monitor:
                if not self.initialize_monitor():
                    return False
            
            self.monitor.check_for_comments()
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking comments: {e}")
            self.logger.error(traceback.format_exc())
            
            # Try to reinitialize monitor on error
            try:
                self.logger.info("Attempting to reinitialize monitor...")
                self.monitor = None
                return self.initialize_monitor()
            except Exception as reinit_error:
                self.logger.error(f"Failed to reinitialize monitor: {reinit_error}")
                return False

    def run_forever(self):
        """Main service loop - runs indefinitely"""
        self.logger.info("🚀 Starting GitHub Issue #1 Persistent Comment Monitor Service")
        self.logger.info(f"⏱️ Poll interval: {self.poll_interval} seconds")
        self.logger.info(f"🎯 Repository: Tenormusica2024/web-remote-desktop")
        self.logger.info(f"🎯 Issue: #1")
        self.logger.info(f"📋 Processing: Only 'upper:' and 'lower:' commands")
        self.logger.info(f"📁 Logs: {Path('logs').resolve()}")
        
        try:
            # Initialize monitor
            if not self.initialize_monitor():
                self.logger.error("❌ Failed to initialize monitor. Exiting.")
                sys.exit(1)
            
            consecutive_failures = 0
            max_failures = 10
            
            while True:
                try:
                    success = self.check_for_comments()
                    
                    if success:
                        consecutive_failures = 0
                    else:
                        consecutive_failures += 1
                        self.logger.warning(f"Consecutive failures: {consecutive_failures}/{max_failures}")
                        
                        if consecutive_failures >= max_failures:
                            self.logger.error(f"❌ Too many consecutive failures ({consecutive_failures}). Restarting...")
                            consecutive_failures = 0
                            time.sleep(30)  # Wait longer before restart
                            continue
                    
                    time.sleep(self.poll_interval)
                    
                except KeyboardInterrupt:
                    self.logger.info("⏹️ Service stopped by user (Ctrl+C)")
                    break
                except Exception as e:
                    consecutive_failures += 1
                    self.logger.error(f"Unexpected error in main loop: {e}")
                    self.logger.error(traceback.format_exc())
                    
                    if consecutive_failures >= max_failures:
                        self.logger.error(f"❌ Too many consecutive failures. Waiting 60s before restart...")
                        time.sleep(60)
                        consecutive_failures = 0
                    else:
                        time.sleep(10)
                        
        except Exception as e:
            self.logger.error(f"Fatal error in service: {e}")
            self.logger.error(traceback.format_exc())
            time.sleep(10)
            self.run_forever()  # Recursive restart

def main():
    """Main entry point"""
    try:
        # Check if running in background
        import os
        if os.name == 'nt':  # Windows
            # Hide console window for background operation
            try:
                import win32gui
                import win32con
                hwnd = win32gui.GetForegroundWindow()
                win32gui.ShowWindow(hwnd, win32con.SW_HIDE)
            except ImportError:
                pass  # win32gui not available, continue anyway
        
        service = PersistentIssue1Service(poll_interval=5)
        service.run_forever()
        
    except KeyboardInterrupt:
        print("\n⏹️ Service stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()