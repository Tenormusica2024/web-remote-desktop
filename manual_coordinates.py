#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Manual coordinate setup for testing
"""
import json
from pathlib import Path

def setup_test_coordinates():
    """Set up test coordinates for the system"""
    # Default coordinates (you can adjust these)
    coords = {
        "upper": [800, 300],  # 右上ペイン想定位置
        "lower": [800, 500]   # 右下ペイン想定位置  
    }
    
    cfg_file = Path(".gh_issue_to_claude_coords.json")
    
    with open(cfg_file, 'w', encoding='utf-8') as f:
        json.dump(coords, f, ensure_ascii=False, indent=2)
    
    print("テスト用座標を設定しました:")
    print(f"  右上ペイン (upper): {coords['upper']}")
    print(f"  右下ペイン (lower): {coords['lower']}")
    print(f"  保存先: {cfg_file.resolve()}")
    print()
    print("注意: これらは仮の座標です。")
    print("正確な座標を設定するには calibrate_system.bat を実行してください。")
    
    return cfg_file.exists()

if __name__ == "__main__":
    setup_test_coordinates()