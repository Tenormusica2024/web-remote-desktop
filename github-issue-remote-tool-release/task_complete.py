#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
タスク完了報告 - GitHub Issue自動投稿スクリプト（汎用版）
Claude Codeの作業完了をGitHub Issueに自動報告
"""

import requests
import sys
import json
from datetime import datetime
from pathlib import Path

class TaskCompleteReporter:
    def __init__(self):
        self.load_config()
        
    def load_config(self):
        """config.jsonから設定読み込み"""
        config_file = Path("config.json")
        if not config_file.exists():
            raise RuntimeError("config.jsonが見つかりません。setup_wizard.pyを実行してください")
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            self.github_token = config.get("github_token")
            self.github_repo = config.get("github_repo")
            self.issue_number = str(config.get("issue_number"))
            
            if not all([self.github_token, self.github_repo, self.issue_number]):
                raise RuntimeError("config.jsonに必須項目が不足しています")
                
        except json.JSONDecodeError as e:
            raise RuntimeError(f"config.json解析エラー: {e}")
        except Exception as e:
            raise RuntimeError(f"設定読み込みエラー: {e}")
    
    def post_completion_comment(self, custom_message=None):
        """GitHub Issueにタスク完了コメントを投稿"""
        try:
            owner, repo = self.github_repo.split("/", 1)
            url = f"https://api.github.com/repos/{owner}/{repo}/issues/{self.issue_number}/comments"
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if custom_message:
                formatted_message = custom_message.replace(" / ", "\n\n").replace("/", "\n\n")
                body = f"🤖 **タスク完了報告**\n\n{formatted_message}\n\n⏰ **完了時刻**: {timestamp}\n\n💻 **実行者**: Claude Code"
            else:
                body = f"🤖 **タスク完了**\n\n⏰ **完了時刻**: {timestamp}\n\n💻 **実行者**: Claude Code"
            
            headers = {
                "Authorization": f"Bearer {self.github_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "github-issue-remote-tool/1.0"
            }
            
            response = requests.post(url, json={"body": body}, headers=headers, timeout=30)
            
            if response.status_code in (200, 201):
                comment_data = response.json()
                print(f"✅ タスク完了報告をGitHub Issueに投稿しました")
                print(f"コメントURL: {comment_data.get('html_url', 'N/A')}")
                print(f"投稿時刻: {timestamp}")
                return True
            else:
                print(f"❌ 投稿失敗: {response.status_code}")
                print(f"エラー詳細: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ エラーが発生しました: {e}")
            return False

def main():
    print("=" * 60)
    print("Claude Code タスク完了報告システム")
    print("=" * 60)
    
    try:
        reporter = TaskCompleteReporter()
        
        if len(sys.argv) > 1:
            custom_message = " ".join(sys.argv[1:])
            print(f"カスタムメッセージ: {custom_message}")
        else:
            custom_message = None
            print("標準完了メッセージを使用します")
        
        print(f"送信先: {reporter.github_repo} Issue #{reporter.issue_number}")
        print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        success = reporter.post_completion_comment(custom_message)
        
        print()
        if success:
            print("✅ タスク完了報告が正常に投稿されました！")
        else:
            print("❌ タスク完了報告の投稿に失敗しました。")
        
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 初期化エラー: {e}")
        print("config.jsonの設定を確認してください。")
        sys.exit(1)

if __name__ == "__main__":
    main()