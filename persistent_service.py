#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Persistent GitHub Comment Monitor Service
24/7 background monitoring with auto-restart and logging
"""
import os
import sys
import time
import json
import logging
import requests
from datetime import datetime
from pathlib import Path
import traceback

class PersistentCommentMonitor:
    def __init__(self):
        self.setup_logging()
        self.setup_environment()
        self.load_modules()
        
        # Service settings
        self.poll_interval = int(os.environ.get('POLL_SEC', '5'))
        self.max_errors = 10  # Max consecutive errors before restart
        self.error_count = 0
        self.total_processed = 0
        self.start_time = datetime.now()
        
        self.logger.info("=== Persistent Comment Monitor Initialized ===")
        self.logger.info(f"Poll interval: {self.poll_interval} seconds")
        self.logger.info(f"Target: {os.environ['GH_REPO']} Issue #{os.environ['GH_ISSUE']}")
    
    def setup_logging(self):
        """Setup rotating log files"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Configure logging
        log_file = log_dir / f"comment_monitor_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_environment(self):
        """Setup environment variables"""
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
    
    def load_modules(self):
        """Load required modules"""
        try:
            from gh_issue_to_claude_paste import (
                parse_pane_and_text, focus_and_paste, session,
                load_json, save_json, STATE_FILE, API, OWNER, REPO, ISSUE_NUM
            )
            self.parse_pane_and_text = parse_pane_and_text
            self.focus_and_paste = focus_and_paste
            self.session = session
            self.load_json = load_json
            self.save_json = save_json
            self.STATE_FILE = STATE_FILE
            self.comments_url = f"{API}/repos/{OWNER}/{REPO}/issues/{ISSUE_NUM}/comments?per_page=10"
            
            self.logger.info("Modules loaded successfully")
        except Exception as e:
            self.logger.error(f"Module loading failed: {e}")
            sys.exit(1)
    
    def check_for_comments(self):
        """Check for new comments and process them"""
        try:
            # Load current state
            state = self.load_json(self.STATE_FILE, {"last_comment_id": 0, "comments_etag": None})
            last_id = int(state.get("last_comment_id", 0))
            comments_etag = state.get("comments_etag")
            
            # Make API request with ETag
            headers = {}
            if comments_etag:
                headers["If-None-Match"] = comments_etag
            
            r = self.session.get(self.comments_url, headers=headers, timeout=20)
            new_etag = r.headers.get("ETag", comments_etag)
            
            if r.status_code == 304:
                # No new comments
                return False
            
            if r.status_code != 200:
                self.logger.warning(f"API returned {r.status_code}: {r.text[:200]}")
                return False
            
            comments = r.json()
            comments.sort(key=lambda c: c.get("id", 0))
            new_comments = [c for c in comments if c.get("id", 0) > last_id]
            
            if new_comments:
                self.logger.info(f"Found {len(new_comments)} new comments")
                
                for c in new_comments:
                    cid = c.get("id", 0)
                    user = c.get("user", {}).get("login", "")
                    body = c.get("body", "")
                    
                    self.logger.info(f"Processing comment #{cid} by @{user}")
                    
                    # Skip if not target user
                    if os.environ.get('ONLY_AUTHOR') and user.lower() != os.environ.get('ONLY_AUTHOR', '').lower():
                        self.logger.info(f"Skipped comment #{cid} (not target user)")
                        last_id = max(last_id, cid)
                        continue
                    
                    # Parse and process
                    pane, text, no_enter = self.parse_pane_and_text(body)
                    if not text.strip():
                        self.logger.info(f"Skipped comment #{cid} (empty text)")
                        last_id = max(last_id, cid)
                        continue
                    
                    auto_enter = not no_enter
                    self.logger.info(f"Comment #{cid}: {pane} pane, {len(text)} chars, Enter={auto_enter}")
                    
                    try:
                        self.focus_and_paste(pane, text, auto_enter)
                        self.logger.info(f"SUCCESS: Comment #{cid} processed and sent to Claude Code")
                        self.total_processed += 1
                    except Exception as e:
                        self.logger.error(f"Failed to process comment #{cid}: {e}")
                    
                    last_id = max(last_id, cid)
                
                # Update state
                state["last_comment_id"] = last_id
                state["comments_etag"] = new_etag
                self.save_json(self.STATE_FILE, state)
                
                # Reset error count on success
                self.error_count = 0
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking comments: {e}")
            self.error_count += 1
            return False
    
    def get_status_info(self):
        """Get current status information"""
        uptime = datetime.now() - self.start_time
        return {
            'uptime': str(uptime),
            'total_processed': self.total_processed,
            'error_count': self.error_count,
            'poll_interval': self.poll_interval
        }
    
    def run_forever(self):
        """Main service loop - runs indefinitely"""
        self.logger.info("Starting persistent monitoring service...")
        
        iteration = 0
        last_status_log = time.time()
        
        try:
            while True:
                iteration += 1
                
                # Check for new comments
                self.check_for_comments()
                
                # Log status every hour
                if time.time() - last_status_log > 3600:  # 1 hour
                    status = self.get_status_info()
                    self.logger.info(f"Status: Uptime={status['uptime']}, Processed={status['total_processed']}, Errors={status['error_count']}")
                    last_status_log = time.time()
                
                # Check for too many consecutive errors
                if self.error_count >= self.max_errors:
                    self.logger.error(f"Too many consecutive errors ({self.error_count}). Restarting service...")
                    self.error_count = 0
                    time.sleep(30)  # Wait before restart
                
                # Sleep before next check
                time.sleep(self.poll_interval)
                
        except KeyboardInterrupt:
            self.logger.info("Service stopped by user (Ctrl+C)")
        except Exception as e:
            self.logger.error(f"Unexpected error in main loop: {e}")
            self.logger.error(traceback.format_exc())
            
            # Auto-restart after critical error
            self.logger.info("Restarting service in 10 seconds...")
            time.sleep(10)
            self.run_forever()  # Recursive restart

def main():
    """Main entry point"""
    monitor = PersistentCommentMonitor()
    monitor.run_forever()

if __name__ == "__main__":
    main()