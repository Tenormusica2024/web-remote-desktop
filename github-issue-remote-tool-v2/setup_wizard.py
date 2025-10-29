#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
セットアップウィザード (v2 - ウィンドウ直接操作方式)
"""

import json
import requests
from pathlib import Path
import pygetwindow as gw

def print_header():
    """ヘッダー表示"""
    print("=" * 60)
    print("GitHub Issue ⇔ Claude Code 遠隔操作ツール")
    print("セットアップウィザード (v2)")
    print("=" * 60)
    print()

def get_github_token():
    """GitHub Personal Access Token取得"""
    print("【ステップ1】GitHub Personal Access Token")
    print("-" * 60)
    print("GitHub Personal Access Tokenを入力してください。")
    print()
    print("トークン作成方法:")
    print("1. https://github.com/settings/tokens を開く")
    print("2. 「Generate new token (classic)」をクリック")
    print("3. 必要なスコープを選択:")
    print("   - プライベートリポジトリ: 'repo' (すべて)")
    print("   - パブリックリポジトリのみ: 'public_repo'")
    print("4. 「Generate token」をクリック")
    print("5. 生成されたトークンをコピー")
    print()
    
    while True:
        token = input("GitHub Token: ").strip()
        if not token:
            print("❌ トークンを入力してください")
            continue
        
        if verify_github_token(token):
            print("✅ トークン検証成功")
            return token
        else:
            print("❌ トークンが無効です。再入力してください。")

def verify_github_token(token):
    """GitHub Token検証"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get("https://api.github.com/user", headers=headers, timeout=10)
        if response.status_code == 200:
            user = response.json()
            print(f"✅ 認証成功: @{user['login']}")
            return True
        else:
            return False
    except Exception as e:
        print(f"❌ 接続エラー: {e}")
        return False

def get_issue_urls(token):
    """Issue URL取得"""
    print()
    print("【ステップ2】監視するGitHub Issue")
    print("-" * 60)
    print("監視するIssue URLを入力してください。")
    print()
    print("形式: https://github.com/owner/repository/issues/番号")
    print("または: ttps://github.com/owner/repository/issues/番号")
    print("例: https://github.com/octocat/Hello-World/issues/1")
    print("    ttps://github.com/octocat/Hello-World/issues/2")
    print()
    print("複数のIssueを監視する場合は、1つずつ追加できます。")
    print()
    
    issues = []
    
    while True:
        if issues:
            print(f"\n現在登録済みのIssue: {len(issues)}個")
            for i, issue_url in enumerate(issues, 1):
                print(f"  {i}. {issue_url}")
            print()
        
        issue_url = input("Issue URL (空Enter=登録完了): ").strip()
        
        if not issue_url:
            if issues:
                break
            else:
                print("❌ 少なくとも1つのIssueを登録してください")
                continue
        
        if verify_issue_url(token, issue_url):
            issues.append(issue_url)
            print(f"✅ Issue登録成功")
        else:
            print("❌ Issue URLが無効です。再入力してください。")
    
    return issues

def verify_repository(token, repo):
    """リポジトリ検証"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"https://api.github.com/repos/{repo}", headers=headers, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ 接続エラー: {e}")
        return False

def verify_issue_url(token, issue_url):
    """Issue URL検証（省略形式・スペース区切りも対応）"""
    try:
        import re
        
        url = issue_url.replace(" ", "")
        
        if url.startswith("ttps://"):
            url = "h" + url
        
        match = re.match(r'https://github\.com/([^/]+)/([^/]+)/issues/(\d+)', url)
        if not match:
            print("❌ URL形式が不正です")
            print("   正しい形式: https://github.com/owner/repo/issues/番号")
            print("   または: ttps://github.com/owner/repo/issues/番号")
            print("   スペース区切りも可: https: //github.com /owner/ repo/ issues/ 番号")
            return False
        
        owner, repo_name, issue_num = match.groups()
        repo = f"{owner}/{repo_name}"
        
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"https://api.github.com/repos/{repo}/issues/{issue_num}",
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            issue = response.json()
            print(f"   リポジトリ: {repo}")
            print(f"   Issue番号: #{issue_num}")
            print(f"   タイトル: {issue['title']}")
            return True
        else:
            print(f"❌ Issue取得失敗: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 接続エラー: {e}")
        return False

def get_poll_interval():
    """ポーリング間隔取得"""
    print()
    print("【ステップ3】ポーリング間隔")
    print("-" * 60)
    print("GitHub Issueを監視する間隔（秒）を設定してください。")
    print("推奨: 5秒（デフォルト）")
    print()
    
    while True:
        interval = input("ポーリング間隔（秒） [5]: ").strip()
        if not interval:
            return 5
        
        if interval.isdigit() and int(interval) > 0:
            return int(interval)
        else:
            print("❌ 正の整数を入力してください")

def detect_claude_windows():
    """Claude Codeウィンドウ検出"""
    print()
    print("【ステップ4】Claude Codeウィンドウ検出")
    print("-" * 60)
    print("起動中のClaude Codeウィンドウを検出します...")
    print()
    
    all_windows = gw.getAllWindows()
    claude_windows = []
    
    for window in all_windows:
        title = window.title.lower()
        if "claude" in title and window.visible:
            claude_windows.append(window)
    
    if not claude_windows:
        print("⚠️ Claude Codeウィンドウが見つかりませんでした")
        print()
        print("【重要】Claude Codeを起動してください:")
        print("1. Claude Codeを起動")
        print("2. このセットアップを再実行")
        print()
        print("監視サービスは起動できますが、コメント転送時にClaude Codeが")
        print("起動していない場合はエラーになります。")
        print()
        input("Enterキーで続行...")
        return 0
    
    print(f"✅ {len(claude_windows)}個のClaude Codeウィンドウを検出しました:")
    print()
    for i, window in enumerate(claude_windows, 1):
        print(f"  #{i}: {window.title}")
        print(f"      位置: ({window.left}, {window.top})")
        print(f"      サイズ: {window.width}x{window.height}")
        print()
    
    print("これらのウィンドウに対して以下のコマンドで指示を送信できます:")
    print("  #1: 指示内容 → 1番目のウィンドウに送信")
    print("  #2: 指示内容 → 2番目のウィンドウに送信")
    print("  (コマンドなし) → デフォルトで1番目に送信")
    print()
    
    return len(claude_windows)

def save_config(token, issue_urls, poll_interval):
    """設定ファイル保存"""
    print()
    print("【ステップ5】設定ファイル保存")
    print("-" * 60)
    
    issues_config = []
    for url in issue_urls:
        issues_config.append({
            "url": url,
            "enabled": True
        })
    
    config = {
        "github_token": token,
        "issues": issues_config,
        "poll_interval": poll_interval
    }
    
    config_file = Path("config.json")
    
    try:
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 設定ファイル保存完了: {config_file.absolute()}")
        print(f"   登録Issue数: {len(issue_urls)}個")
        return True
    except Exception as e:
        print(f"❌ 設定ファイル保存エラー: {e}")
        return False

def show_usage():
    """使い方表示"""
    print()
    print("=" * 60)
    print("🎉 セットアップ完了！")
    print("=" * 60)
    print()
    print("【次のステップ】")
    print()
    print("1. 監視サービス起動:")
    print("   python monitor_service.py")
    print()
    print("2. GitHub Issueにコメント:")
    print("   #1: このファイルのバグを修正して")
    print("   #2: プロジェクトの進捗を教えて")
    print("   ss  (スクリーンショット)")
    print()
    print("3. 完了報告:")
    print("   Claude Code側で task_complete.py を実行")
    print()
    print("詳細はREADME.mdを参照してください。")
    print("=" * 60)

def main():
    print_header()
    
    token = get_github_token()
    issue_urls = get_issue_urls(token)
    poll_interval = get_poll_interval()
    
    num_windows = detect_claude_windows()
    
    if save_config(token, issue_urls, poll_interval):
        show_usage()
    else:
        print("❌ セットアップ失敗")
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        exit(main())
    except KeyboardInterrupt:
        print("\n\n⏹️ セットアップをキャンセルしました")
        exit(1)
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        input("\nEnterキーで終了...")
        exit(1)