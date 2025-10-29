#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Claude Codeウィンドウ検出テストスクリプト
"""

import pygetwindow as gw
import pyautogui
import pyperclip
import time

def detect_claude_windows():
    """すべてのClaude Codeウィンドウを検出"""
    all_windows = gw.getAllWindows()
    claude_windows = []
    
    for window in all_windows:
        title = window.title.lower()
        # "claude" を含むウィンドウを検出
        if "claude" in title and window.visible:
            claude_windows.append(window)
    
    return claude_windows

def list_claude_windows():
    """Claude Codeウィンドウ一覧を表示"""
    windows = detect_claude_windows()
    
    if not windows:
        print("❌ Claude Codeウィンドウが見つかりません")
        return None
    
    print(f"\n✅ {len(windows)}個のClaude Codeウィンドウを検出しました:\n")
    for i, window in enumerate(windows, 1):
        print(f"#{i}: {window.title}")
        print(f"    位置: ({window.left}, {window.top})")
        print(f"    サイズ: {window.width}x{window.height}")
        print(f"    最小化: {window.isMinimized}")
        print(f"    アクティブ: {window.isActive}")
        print()
    
    return windows

def send_text_method1(window, text):
    """方法1: ウィンドウアクティブ化 + クリップボード + Ctrl+V"""
    try:
        print("方法1: ウィンドウアクティブ化 + Ctrl+V")
        
        # ウィンドウをアクティブ化
        if window.isMinimized:
            window.restore()
        window.activate()
        time.sleep(0.3)
        
        # クリップボードに保存
        old_clip = pyperclip.paste()
        pyperclip.copy(text)
        time.sleep(0.1)
        
        # Ctrl+V で貼り付け
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.2)
        
        # Enter で送信
        pyautogui.press("enter")
        time.sleep(0.1)
        
        # クリップボード復元
        pyperclip.copy(old_clip)
        
        print("✅ 方法1: 成功")
        return True
    except Exception as e:
        print(f"❌ 方法1: 失敗 - {e}")
        return False

def send_text_method2(window, text):
    """方法2: ウィンドウアクティブ化 + typewrite（遅い）"""
    try:
        print("方法2: ウィンドウアクティブ化 + typewrite")
        
        # ウィンドウをアクティブ化
        if window.isMinimized:
            window.restore()
        window.activate()
        time.sleep(0.3)
        
        # 直接タイプ（英数字のみ対応）
        pyautogui.typewrite(text, interval=0.01)
        time.sleep(0.2)
        
        # Enter で送信
        pyautogui.press("enter")
        time.sleep(0.1)
        
        print("✅ 方法2: 成功")
        return True
    except Exception as e:
        print(f"❌ 方法2: 失敗 - {e}")
        return False

def send_text_method3(window, text):
    """方法3: ウィンドウアクティブ化 + クリック推測 + Ctrl+V"""
    try:
        print("方法3: ウィンドウアクティブ化 + 中央クリック + Ctrl+V")
        
        # ウィンドウをアクティブ化
        if window.isMinimized:
            window.restore()
        window.activate()
        time.sleep(0.3)
        
        # ウィンドウの中央下部をクリック（入力欄を推測）
        center_x = window.left + window.width // 2
        center_y = window.top + int(window.height * 0.9)  # 下部90%の位置
        
        pyautogui.click(center_x, center_y)
        time.sleep(0.2)
        
        # クリップボードに保存
        old_clip = pyperclip.paste()
        pyperclip.copy(text)
        time.sleep(0.1)
        
        # Ctrl+V で貼り付け
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.2)
        
        # Enter で送信
        pyautogui.press("enter")
        time.sleep(0.1)
        
        # クリップボード復元
        pyperclip.copy(old_clip)
        
        print("✅ 方法3: 成功")
        return True
    except Exception as e:
        print(f"❌ 方法3: 失敗 - {e}")
        return False

def test_send_text():
    """テキスト送信テスト"""
    windows = detect_claude_windows()
    
    if not windows:
        print("❌ Claude Codeウィンドウが見つかりません")
        return
    
    print(f"\n✅ {len(windows)}個のClaude Codeウィンドウを検出")
    print("\n最初のウィンドウにテストメッセージを送信します...")
    print("ウィンドウ:", windows[0].title)
    
    test_message = "Test message from window detector"
    
    print("\n5秒後に送信を開始します。Claude Codeを確認してください...")
    for i in range(5, 0, -1):
        print(f"{i}...", end=" ", flush=True)
        time.sleep(1)
    print("\n")
    
    # 方法1を試行
    success = send_text_method1(windows[0], test_message)
    
    if not success:
        print("\n方法1が失敗しました。方法3を試行します...\n")
        time.sleep(2)
        success = send_text_method3(windows[0], test_message)
    
    if success:
        print("\n✅ テキスト送信テスト完了")
    else:
        print("\n❌ すべての方法が失敗しました")

def main():
    print("=" * 60)
    print("Claude Code ウィンドウ検出テスト")
    print("=" * 60)
    
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "list":
            list_claude_windows()
        elif sys.argv[1] == "test":
            test_send_text()
    else:
        print("\n使用方法:")
        print("  python window_detector_test.py list  - ウィンドウ一覧表示")
        print("  python window_detector_test.py test  - テキスト送信テスト")

if __name__ == "__main__":
    main()