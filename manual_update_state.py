#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Manual state update for Issue #3
"""
import json
from pathlib import Path

# Update Issue #3 state to latest comment
state_file = Path(".gh_issue_to_claude_state.json")
new_state = {
    "last_comment_id": 3235071704,  # Latest comment ID
    "comments_etag": None  # Force refresh
}

with open(state_file, 'w', encoding='utf-8') as f:
    json.dump(new_state, f, ensure_ascii=False, indent=2)

print(f"Updated Issue #3 state to comment ID: {new_state['last_comment_id']}")

# Check current state for Issue #1
issue1_state_file = Path(".gh_issue1_to_claude_state.json")
if issue1_state_file.exists():
    with open(issue1_state_file, 'r', encoding='utf-8') as f:
        issue1_state = json.load(f)
    print(f"Issue #1 last comment ID: {issue1_state['last_comment_id']}")
else:
    print("Issue #1 state file not found")