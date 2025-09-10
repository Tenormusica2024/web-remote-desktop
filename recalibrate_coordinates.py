#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Coordinate Recalibration Tool
Fix upper/lower pane coordinates
"""
import json
import pyautogui
import time
from pathlib import Path

def recalibrate_coordinates():
    """Interactively recalibrate coordinates"""
    print("=== Coordinate Recalibration ===")
    print("This will help you set the correct coordinates for upper and lower panes.")
    print()
    
    # Get screen size
    width, height = pyautogui.size()
    print(f"Screen size: {width}x{height}")
    print()
    
    print("Instructions:")
    print("1. Make sure Claude Code is open and visible")
    print("2. The upper pane should be in the RIGHT-TOP area")
    print("3. The lower pane should be in the RIGHT-BOTTOM area")
    print()
    
    input("Press Enter when ready...")
    
    print("\nStep 1: Upper Pane (Right-Top)")
    print("Move your mouse to the INPUT AREA of the RIGHT-TOP pane")
    print("Press Enter when positioned...")
    input()
    
    upper_x, upper_y = pyautogui.position()
    print(f"Upper pane recorded: ({upper_x}, {upper_y})")
    
    print("\nStep 2: Lower Pane (Right-Bottom)")  
    print("Move your mouse to the INPUT AREA of the RIGHT-BOTTOM pane")
    print("Press Enter when positioned...")
    input()
    
    lower_x, lower_y = pyautogui.position()
    print(f"Lower pane recorded: ({lower_x}, {lower_y})")
    
    # Show the coordinates
    print(f"\n=== New Coordinates ===")
    print(f"Upper (right-top): [{upper_x}, {upper_y}]")
    print(f"Lower (right-bottom): [{lower_x}, {lower_y}]")
    
    # Verify coordinates make sense
    if upper_y >= lower_y:
        print("\nWARNING: Upper pane Y coordinate should be SMALLER than lower pane")
        print(f"Upper Y: {upper_y}, Lower Y: {lower_y}")
        print("Make sure upper pane is ABOVE the lower pane")
    
    if abs(upper_x - lower_x) > 200:
        print(f"\nWARNING: X coordinates are very different")
        print(f"Upper X: {upper_x}, Lower X: {lower_x}")
        print("Both panes should be in the RIGHT side of Claude Code")
    
    # Save coordinates
    coords = {
        "upper": [upper_x, upper_y],
        "lower": [lower_x, lower_y]
    }
    
    coord_file = Path(".gh_issue_to_claude_coords.json")
    with open(coord_file, 'w', encoding='utf-8') as f:
        json.dump(coords, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Coordinates saved to: {coord_file.resolve()}")
    
    # Test by moving mouse to each position
    print(f"\n=== Testing Coordinates ===")
    
    print("Moving to upper pane...")
    pyautogui.moveTo(upper_x, upper_y, duration=1)
    time.sleep(2)
    
    print("Moving to lower pane...")
    pyautogui.moveTo(lower_x, lower_y, duration=1)
    time.sleep(2)
    
    print("\n✅ Recalibration complete!")
    print("Now test with: upper: test message")

if __name__ == "__main__":
    recalibrate_coordinates()