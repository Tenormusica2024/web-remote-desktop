#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Issue #1 to Claude Code Paste System
Repository: web-remote-desktop
Issue: #1
Only processes comments starting with 'upper:' or 'lower:'
"""

import os
import sys
import requests
import json
import time
import pyautogui
import pyperclip
import logging
import traceback
from pathlib import Path
from typing import Dict, Optional, Tuple, List

class GitHubIssue1CommentMonitor:
    def __init__(self):
        """Initialize GitHub Issue #1 comment monitor"""
        self.repo_owner = "Tenormusica2024"
        self.repo_name = "web-remote-desktop" 
        self.issue_number = 1
        self.github_token = self.load_github_token()
        
        # State files
        self.state_file = Path(".gh_issue1_to_claude_state.json")
        self.coords_file = Path(".gh_issue_to_claude_coords.json")  # Reuse same coordinates
        
        # Setup logging first
        self.setup_logging()
        
        # Load configuration
        self.coordinates = self.load_coordinates()
        self.state = self.load_state()
        
        # API settings
        self.base_url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}"
        self.headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "GitHub-Issue1-Claude-Monitor/1.0"
        }
        
        self.logger.info("GitHub Issue #1 comment monitor initialized")
        self.logger.info(f"Repository: {self.repo_owner}/{self.repo_name}")
        self.logger.info(f"Issue: #{self.issue_number}")
        self.logger.info(f"Coordinates: {self.coordinates}")

    def load_github_token(self) -> str:
        """Load GitHub personal access token from environment variable"""
        token = os.getenv('GITHUB_TOKEN')
        if not token:
            print("ERROR: GITHUB_TOKEN environment variable not set!")
            print("Please set your GitHub Personal Access Token:")
            print("  Windows: set GITHUB_TOKEN=ghp_your_token_here")
            print("  PowerShell: $env:GITHUB_TOKEN='ghp_your_token_here'")
            print("  Linux/Mac: export GITHUB_TOKEN=ghp_your_token_here")
            sys.exit(1)
        return token.strip()

    def load_coordinates(self) -> Dict[str, List[int]]:
        """Load mouse coordinates for panes"""
        if self.coords_file.exists():
            with open(self.coords_file, 'r', encoding='utf-8') as f:
                coords = json.load(f)
                self.logger.info(f"Loaded coordinates: {coords}")
                return coords
        else:
            # Default coordinates (reuse from Issue #3 system)
            default_coords = {
                "upper": [2880, 400],
                "lower": [2880, 1404]
            }
            self.save_coordinates(default_coords)
            return default_coords

    def save_coordinates(self, coordinates: Dict[str, List[int]]):
        """Save coordinates to file"""
        with open(self.coords_file, 'w', encoding='utf-8') as f:
            json.dump(coordinates, f, ensure_ascii=False, indent=2)
        self.logger.info(f"Coordinates saved: {coordinates}")

    def load_state(self) -> Dict:
        """Load processing state"""
        if self.state_file.exists():
            with open(self.state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
                self.logger.info(f"Loaded state: {state}")
                return state
        else:
            # Initial state
            initial_state = {
                "last_comment_id": 0,
                "comments_etag": None
            }
            self.save_state(initial_state)
            return initial_state

    def save_state(self, state: Dict):
        """Save processing state"""
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

    def setup_logging(self):
        """Setup logging configuration"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f"issue1_monitor_{time.strftime('%Y%m%d')}.log"
        
        self.logger = logging.getLogger("Issue1Monitor")
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

    def get_issue_comments(self) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """Fetch ALL issue comments with pagination support"""
        base_url = f"{self.base_url}/issues/{self.issue_number}/comments"
        all_comments = []
        page = 1
        
        try:
            while True:
                url = f"{base_url}?per_page=100&page={page}"
                self.logger.debug(f"Fetching page {page}: {url}")
                
                response = requests.get(url, headers=self.headers, timeout=10)
                
                if response.status_code != 200:
                    self.logger.error(f"API error: {response.status_code} - {response.text}")
                    return None, None
                
                page_comments = response.json()
                if not page_comments:
                    # No more comments
                    break
                
                all_comments.extend(page_comments)
                self.logger.debug(f"Page {page}: {len(page_comments)} comments")
                
                # Check if there are more pages
                link_header = response.headers.get('Link', '')
                if 'rel="next"' not in link_header:
                    break
                
                page += 1
            
            self.logger.info(f"Retrieved {len(all_comments)} total comments from all pages")
            etag = response.headers.get('ETag') if 'response' in locals() else None
            return all_comments, etag
            
        except requests.RequestException as e:
            self.logger.error(f"Request failed: {e}")
            return None, None

    def parse_pane_command(self, comment_body: str) -> Optional[Tuple[str, str]]:
        """
        Parse pane command from comment
        Only accepts comments starting with 'upper:' or 'lower:'
        Returns (pane, text) or None if no valid command found
        """
        comment_body = comment_body.strip()
        
        # Check for upper: command
        if comment_body.lower().startswith('upper:'):
            text = comment_body[6:].strip()  # Remove 'upper:' prefix
            if text:  # Only if there's actual text after the colon
                return 'upper', text
        
        # Check for lower: command  
        elif comment_body.lower().startswith('lower:'):
            text = comment_body[6:].strip()  # Remove 'lower:' prefix
            if text:  # Only if there's actual text after the colon
                return 'lower', text
        
        # No valid command found - ignore this comment
        return None

    def focus_and_paste(self, pane: str, text: str, auto_enter: bool = True):
        """Focus pane and paste text with optional auto-enter"""
        try:
            # Get coordinates
            if pane not in self.coordinates:
                self.logger.error(f"Unknown pane: {pane}")
                return False
            
            x, y = self.coordinates[pane]
            self.logger.info(f"Focusing {pane} pane at ({x}, {y})")
            
            # Click to focus
            pyautogui.click(x, y)
            time.sleep(0.2)
            
            # Copy text to clipboard and paste
            pyperclip.copy(text)
            time.sleep(0.1)
            
            pyautogui.hotkey("ctrl", "v")
            time.sleep(0.2)
            
            # Auto-enter if requested
            if auto_enter:
                pyautogui.press("enter")
                time.sleep(0.1)
            
            self.logger.info(f"Successfully pasted to {pane} pane: '{text[:50]}...' (auto_enter: {auto_enter})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to paste to {pane} pane: {e}")
            return False

    def process_new_comments(self, comments: List[Dict]) -> int:
        """Process new comments and send to Claude Code"""
        processed_count = 0
        last_comment_id = self.state["last_comment_id"]
        
        # Sort by comment ID to process in order
        new_comments = [c for c in comments if c["id"] > last_comment_id]
        new_comments.sort(key=lambda x: x["id"])
        
        self.logger.info(f"Found {len(new_comments)} new comments to process")
        
        for comment in new_comments:
            try:
                comment_id = comment["id"]
                comment_body = comment["body"]
                author = comment["user"]["login"]
                created_at = comment["created_at"]
                
                self.logger.info(f"Processing comment {comment_id} by {author}: '{comment_body[:100]}...'")
                
                # Parse pane command
                pane_command = self.parse_pane_command(comment_body)
                
                if pane_command:
                    pane, text = pane_command
                    self.logger.info(f"Valid command found: {pane} -> '{text[:50]}...'")
                    
                    # Send to Claude Code
                    success = self.focus_and_paste(pane, text, auto_enter=True)
                    
                    if success:
                        processed_count += 1
                        self.logger.info(f"✅ Comment {comment_id} processed successfully -> {pane} pane")
                    else:
                        self.logger.error(f"❌ Failed to process comment {comment_id}")
                else:
                    self.logger.info(f"⏭️ Comment {comment_id} ignored (no upper:/lower: prefix)")
                
                # Small delay between comments
                time.sleep(0.5)
                
            except Exception as e:
                self.logger.error(f"Error processing comment {comment.get('id', 'unknown')}: {e}")
                self.logger.error(traceback.format_exc())
        
        # Update state with highest processed comment ID
        if new_comments:
            highest_id = max(c["id"] for c in new_comments)
            self.state["last_comment_id"] = highest_id
            self.save_state(self.state)
            
        return processed_count

    def check_for_comments(self):
        """Check for new comments and process them"""
        try:
            self.logger.info("Checking for new comments...")
            
            comments, new_etag = self.get_issue_comments()
            
            if comments is None:
                self.logger.info("No new comments found")
                return
            
            # Process new comments
            processed_count = self.process_new_comments(comments)
            
            # Update state
            if new_etag:
                self.state["comments_etag"] = new_etag
            
            self.save_state(self.state)
            
            if processed_count > 0:
                self.logger.info(f"✅ Processed {processed_count} comments successfully")
            else:
                self.logger.info("No new comments to process")
                
        except Exception as e:
            self.logger.error(f"Error in check_for_comments: {e}")
            self.logger.error(traceback.format_exc())

    def run_once(self):
        """Run one check cycle"""
        self.logger.info("=== GitHub Issue #1 Comment Monitor - Single Run ===")
        self.check_for_comments()
    
    def run_continuous(self, poll_interval=10):
        """Run continuous monitoring"""
        self.logger.info("=== GitHub Issue #1 Comment Monitor - Continuous Mode ===")
        self.logger.info(f"Polling interval: {poll_interval} seconds")
        
        try:
            while True:
                self.check_for_comments()
                time.sleep(poll_interval)
        except KeyboardInterrupt:
            self.logger.info("Monitoring stopped by user")
        except Exception as e:
            self.logger.error(f"Error in continuous monitoring: {e}")

def main():
    """Main entry point"""
    try:
        monitor = GitHubIssue1CommentMonitor()
        
        # Check for command line arguments
        if "--once" in sys.argv:
            monitor.run_once()
        else:
            # Default: continuous monitoring
            poll_interval = 10  # seconds
            if "--interval" in sys.argv:
                try:
                    idx = sys.argv.index("--interval")
                    poll_interval = int(sys.argv[idx + 1])
                except (IndexError, ValueError):
                    poll_interval = 10
            
            monitor.run_continuous(poll_interval)
            
    except KeyboardInterrupt:
        print("\nStopped by user")
    except Exception as e:
        try:
            print(f"Fatal error: {e}")
        except UnicodeEncodeError:
            print(f"Fatal error: {str(e).encode('ascii', errors='replace').decode('ascii')}")
        traceback.print_exc()

if __name__ == "__main__":
    main()