#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Issue ⇔ Claude Code 連携ツール - セットアップウィザード
初級者向けの対話型セットアップツール
"""

import json
import os
import sys
import time
import pyautogui
import requests
from pathlib import Path

class SetupWizard:
    def __init__(self):
        self.config = {}
        self.config_file = Path("config.json")
        
    def print_header(self, text):
        """ヘッダー表示"""
        print("\n" + "=" * 60)
        print(text)
        print("=" * 60 + "\n")
        
    def print_step(self, step_num, total_steps, title):
        """ステップタイトル表示"""
        print(f"\n{'─' * 60}")
        print(f"ステップ {step_num}/{total_steps}: {title}")
        print("─" * 60 + "\n")
        
    def input_with_default(self, prompt, default=""):
        """デフォルト値付き入力"""
        if default:
            user_input = input(f"{prompt} [{default}]: ").strip()
            return user_input if user_input else default
        return input(f"{prompt}: ").strip()
        
    def validate_github_token(self, token):
        """GitHubトークン検証"""
        try:
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json"
            }
            r = requests.get("https://api.github.com/user", headers=headers, timeout=10)
            if r.status_code == 200:
                user_data = r.json()
                return True, user_data.get("login", "Unknown")
            return False, f"認証失敗: {r.status_code}"
        except Exception as e:
            return False, f"エラー: {e}"
            
    def validate_repository(self, token, repo):
        """リポジトリ存在確認"""
        try:
            owner, repo_name = repo.split("/", 1)
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json"
            }
            url = f"https://api.github.com/repos/{owner}/{repo_name}"
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                return True, "リポジトリ接続確認完了"
            return False, f"リポジトリが見つかりません: {r.status_code}"
        except Exception as e:
            return False, f"エラー: {e}"
            
    def validate_issue(self, token, repo, issue_num):
        """Issue存在確認"""
        try:
            owner, repo_name = repo.split("/", 1)
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json"
            }
            url = f"https://api.github.com/repos/{owner}/{repo_name}/issues/{issue_num}"
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                issue_data = r.json()
                title = issue_data.get("title", "")
                return True, f"Issue確認完了: {title}"
            return False, f"Issue #{issue_num} が見つかりません: {r.status_code}"
        except Exception as e:
            return False, f"エラー: {e}"
            
    def detect_claude_code_window(self):
        """Claude Codeウィンドウ検出"""
        try:
            import pygetwindow as gw
            windows = gw.getWindowsWithTitle("Claude")
            if windows:
                return True, windows[0].title
            return False, "Claude Codeウィンドウが見つかりません"
        except ImportError:
            return True, "自動検出をスキップ（pygetwindow未インストール）"
        except Exception as e:
            return False, f"エラー: {e}"
            
    def get_mouse_position(self, prompt_text):
        """マウス座標取得"""
        print(f"\n{prompt_text}")
        print("カーソルを目的の位置に移動して、Enterキーを押してください...")
        input()
        
        x, y = pyautogui.position()
        print(f"✅ 座標取得完了: ({x}, {y})")
        return [x, y]
        
    def step1_github_auth(self):
        """ステップ1: GitHub認証情報"""
        self.print_step(1, 5, "GitHub認証情報")
        
        print("GitHub Personal Access Tokenを入力してください:")
        print("トークン作成方法: https://github.com/settings/tokens")
        print("\n必要なスコープ:")
        print("  - repo（プライベートリポジトリの場合）")
        print("  - public_repo（パブリックリポジトリのみの場合）")
        print()
        
        while True:
            token = self.input_with_default("トークン")
            if not token:
                print("❌ トークンを入力してください")
                continue
                
            print("\n検証中...")
            valid, message = self.validate_github_token(token)
            if valid:
                print(f"✅ トークン検証成功: @{message}")
                self.config["github_token"] = token
                break
            else:
                print(f"❌ {message}")
                retry = input("再試行しますか？ (Y/n): ").strip().lower()
                if retry == 'n':
                    sys.exit(1)
                    
    def step2_repository_info(self):
        """ステップ2: リポジトリ情報"""
        self.print_step(2, 5, "リポジトリ情報")
        
        print("監視するGitHub Issueの情報を入力してください:\n")
        
        while True:
            repo = self.input_with_default("リポジトリ名（例: username/repository）")
            if not repo or "/" not in repo:
                print("❌ 形式が正しくありません（例: username/repository）")
                continue
                
            print("\n検証中...")
            valid, message = self.validate_repository(self.config["github_token"], repo)
            if valid:
                print(f"✅ {message}")
                self.config["github_repo"] = repo
                break
            else:
                print(f"❌ {message}")
                retry = input("再試行しますか？ (Y/n): ").strip().lower()
                if retry == 'n':
                    sys.exit(1)
                    
        print()
        while True:
            issue_num = self.input_with_default("Issue番号")
            if not issue_num.isdigit():
                print("❌ 数字を入力してください")
                continue
                
            print("\n検証中...")
            valid, message = self.validate_issue(
                self.config["github_token"], 
                self.config["github_repo"], 
                issue_num
            )
            if valid:
                print(f"✅ {message}")
                self.config["issue_number"] = issue_num
                break
            else:
                print(f"❌ {message}")
                retry = input("再試行しますか？ (Y/n): ").strip().lower()
                if retry == 'n':
                    sys.exit(1)
                    
        poll_interval = self.input_with_default("ポーリング間隔（秒）", "5")
        self.config["poll_interval"] = int(poll_interval)
        
    def step3_claude_code_coords(self):
        """ステップ3: Claude Code座標設定"""
        self.print_step(3, 5, "Claude Code座標検出")
        
        print("Claude Codeウィンドウの入力欄座標を特定します。\n")
        
        # ウィンドウ検出
        valid, message = self.detect_claude_code_window()
        if valid:
            print(f"✅ {message}\n")
        else:
            print(f"⚠️ {message}")
            print("続行しますが、Claude Codeが起動していることを確認してください。\n")
            
        print("⚠️ これからClaude Codeウィンドウの入力欄座標を特定します")
        print("   以下の手順に従ってください:\n")
        
        # 上部入力欄
        upper_coords = self.get_mouse_position("1. Claude Codeウィンドウをアクティブにして、「上部の入力欄」にカーソルを移動してください")
        
        # 下部入力欄
        lower_coords = self.get_mouse_position("\n2. 「下部の入力欄」にカーソルを移動してください")
        
        self.config["claude_code_coords"] = {
            "upper": upper_coords,
            "lower": lower_coords
        }
        
        print("\n座標を手動調整しますか？ (y/N): ", end="")
        if input().strip().lower() == 'y':
            print("\n現在の座標:")
            print(f"  上部入力欄: {upper_coords}")
            print(f"  下部入力欄: {lower_coords}\n")
            
            adjust_upper = input("上部座標を調整しますか？ (y/N): ").strip().lower()
            if adjust_upper == 'y':
                x = int(input("X座標: "))
                y = int(input("Y座標: "))
                self.config["claude_code_coords"]["upper"] = [x, y]
                
            adjust_lower = input("下部座標を調整しますか？ (y/N): ").strip().lower()
            if adjust_lower == 'y':
                x = int(input("X座標: "))
                y = int(input("Y座標: "))
                self.config["claude_code_coords"]["lower"] = [x, y]
                
    def step4_save_config(self):
        """ステップ4: 設定ファイル生成"""
        self.print_step(4, 5, "設定ファイル生成")
        
        print("以下の設定ファイルを生成します:\n")
        print(f"  - {self.config_file.name}")
        print()
        
        confirm = input("生成しますか？ (Y/n): ").strip().lower()
        if confirm == 'n':
            print("キャンセルしました")
            sys.exit(0)
            
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            print(f"\n✅ 設定ファイル生成完了: {self.config_file}")
        except Exception as e:
            print(f"\n❌ 設定ファイル生成エラー: {e}")
            sys.exit(1)
            
    def step5_connection_test(self):
        """ステップ5: 接続テスト"""
        self.print_step(5, 5, "接続テスト")
        
        print("GitHub Issueへの接続をテストしています...\n")
        
        # Issue読み取りテスト
        try:
            owner, repo_name = self.config["github_repo"].split("/", 1)
            headers = {
                "Authorization": f"Bearer {self.config['github_token']}",
                "Accept": "application/vnd.github+json"
            }
            url = f"https://api.github.com/repos/{owner}/{repo_name}/issues/{self.config['issue_number']}"
            r = requests.get(url, headers=headers, timeout=10)
            
            if r.status_code == 200:
                print("✅ Issue読み取り成功")
                issue_data = r.json()
                print(f"   タイトル: {issue_data.get('title', '')}")
            else:
                print(f"❌ Issue読み取り失敗: {r.status_code}")
                
            # コメント取得テスト
            url_comments = f"{url}/comments"
            r = requests.get(url_comments, headers=headers, timeout=10)
            if r.status_code == 200:
                comments = r.json()
                print(f"✅ コメント取得成功（{len(comments)}個のコメント）")
            else:
                print(f"❌ コメント取得失敗: {r.status_code}")
                
            # 座標ファイル確認
            print("✅ 座標設定読み込み成功")
            print(f"   上部入力欄: {self.config['claude_code_coords']['upper']}")
            print(f"   下部入力欄: {self.config['claude_code_coords']['lower']}")
            
        except Exception as e:
            print(f"❌ 接続テストエラー: {e}")
            sys.exit(1)
            
    def show_completion(self):
        """完了メッセージ"""
        self.print_header("🎉 セットアップ完了！")
        
        print("監視サービス起動コマンド:")
        print(f"  python monitor_service.py")
        print()
        print("完了報告ツール使用コマンド:")
        print(f'  python task_complete.py "作業完了メッセージ"')
        print()
        print("ドキュメント: README.md")
        print()
        
    def run(self):
        """ウィザード実行"""
        self.print_header("🎯 GitHub Issue ⇔ Claude Code 連携ツール セットアップ")
        
        self.step1_github_auth()
        self.step2_repository_info()
        self.step3_claude_code_coords()
        self.step4_save_config()
        self.step5_connection_test()
        self.show_completion()

def main():
    wizard = SetupWizard()
    try:
        wizard.run()
    except KeyboardInterrupt:
        print("\n\nセットアップをキャンセルしました")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n予期しないエラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()