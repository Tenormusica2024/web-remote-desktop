#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automatic calibration - find Claude Code input panes
"""
import pyautogui
import time
import json
from pathlib import Path

def auto_find_claude_panes():
    """Try to automatically find Claude Code input panes"""
    print("=== 自動キャリブレーション開始 ===")
    
    # Get screen size
    width, height = pyautogui.size()
    print(f"画面サイズ: {width}x{height}")
    
    # Typical Claude Code layout positions (based on common layouts)
    # These are educated guesses for where the panes typically are
    
    # For a 3840x2160 screen, typical positions might be:
    upper_x = int(width * 0.75)   # 75% from left (right side)
    upper_y = int(height * 0.25)  # 25% from top (upper area)
    
    lower_x = int(width * 0.75)   # 75% from left (right side)  
    lower_y = int(height * 0.65)  # 65% from top (lower area)
    
    coords = {
        "upper": [upper_x, upper_y],
        "lower": [lower_x, lower_y]
    }
    
    print(f"推定座標:")
    print(f"  右上ペイン (upper): {coords['upper']}")
    print(f"  右下ペイン (lower): {coords['lower']}")
    
    # Save coordinates
    cfg_file = Path(".gh_issue_to_claude_coords.json")
    with open(cfg_file, 'w', encoding='utf-8') as f:
        json.dump(coords, f, ensure_ascii=False, indent=2)
    
    print(f"座標を保存しました: {cfg_file.resolve()}")
    
    # Visual test - move mouse to each position briefly
    print("\n座標テスト中...")
    
    print("右上ペインの推定位置に移動...")
    pyautogui.moveTo(coords["upper"][0], coords["upper"][1], duration=1)
    time.sleep(2)
    
    print("右下ペインの推定位置に移動...")
    pyautogui.moveTo(coords["lower"][0], coords["lower"][1], duration=1)
    time.sleep(2)
    
    return coords

if __name__ == "__main__":
    auto_find_claude_panes()
    print("\n✅ 自動キャリブレーション完了")
    print("座標が正確でない場合は、手動でcalibrate_system.batを実行してください")