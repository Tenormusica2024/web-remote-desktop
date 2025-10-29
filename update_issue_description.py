#!/usr/bin/env python3
"""
GitHub Issue 説明文更新スクリプト
最新コメントへのクイックリンクを Issue 本体に追加
"""

import os
import requests
import json
from datetime import datetime

# GitHub APIトークンを環境変数から取得
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "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")

REPO_OWNER = "Tenormusica2024"
REPO_NAME = "Private"
ISSUE_NUMBER = 1

# GitHub API ヘッダー
headers = {
    'Authorization': f'Bearer {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
    'User-Agent': 'claude-code-issue-updater/1.0'
}

def get_latest_comments(count=10):
    """最新のコメントを取得"""
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/issues/{ISSUE_NUMBER}/comments"
    
    params = {
        'per_page': count,
        'sort': 'created',
        'direction': 'desc'
    }
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"エラー: コメント取得失敗 (Status: {response.status_code})")
        return None

def get_issue():
    """Issue 本体を取得"""
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/issues/{ISSUE_NUMBER}"
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"エラー: Issue取得失敗 (Status: {response.status_code})")
        return None

def update_issue_description(new_body):
    """Issue の説明文を更新"""
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/issues/{ISSUE_NUMBER}"
    
    data = {
        'body': new_body
    }
    
    response = requests.patch(url, headers=headers, json=data)
    
    if response.status_code == 200:
        print("✅ Issue 説明文更新成功")
        return response.json()
    else:
        print(f"❌ Issue 説明文更新失敗 (Status: {response.status_code})")
        print(response.text)
        return None

def create_updated_description(original_body, latest_comments):
    """更新された説明文を生成"""
    
    # 最新コメントリンクセクション作成
    quick_links = "\n\n---\n\n# 最新コメントへのクイックアクセス\n\n"
    quick_links += f"**最終更新**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    quick_links += "## 最新10件のコメント（新しい順）\n\n"
    
    for i, comment in enumerate(latest_comments, 1):
        created_at = comment['created_at'][:10]  # YYYY-MM-DD
        comment_id = comment['id']
        comment_url = comment['html_url']
        user = comment['user']['login']
        
        # コメント本文の最初の50文字を取得
        body_preview = comment['body'][:50].replace('\n', ' ')
        if len(comment['body']) > 50:
            body_preview += "..."
        
        quick_links += f"{i}. [{created_at}] [{user}]({comment_url}): {body_preview}\n"
    
    quick_links += "\n### ヒント\n"
    quick_links += "- 上記のリンクをクリックすると該当コメントに直接ジャンプします\n"
    quick_links += "- Ctrl+F で日付検索も可能です\n"
    quick_links += "- GitHub CLI: `gh issue view 1 --repo Tenormusica2024/Private --comments | tail -50`\n"
    
    # 既存の「最新コメント」セクションを削除
    if "最新コメントへのクイックアクセス" in original_body:
        # 既存のセクションを新しいもので置き換え
        parts = original_body.split("---")
        # 最初のセクション（オリジナルの説明）のみ保持
        if len(parts) > 0:
            original_body = parts[0].rstrip()
    
    # 新しい説明文を構築
    new_body = original_body + quick_links
    
    return new_body

def main():
    print("=" * 60)
    print("GitHub Issue 説明文更新スクリプト")
    print("=" * 60)
    
    # Issue 取得
    print("\nIssue 取得中...")
    issue = get_issue()
    
    if not issue:
        print("NG Issue 取得失敗")
        return
    
    print(f"OK Issue タイトル: {issue['title']}")
    
    # 最新コメント取得
    print("\n最新コメント取得中...")
    latest_comments = get_latest_comments(10)
    
    if not latest_comments:
        print("NG コメント取得失敗")
        return
    
    print(f"OK 最新コメント {len(latest_comments)} 件取得")
    
    # 説明文更新
    print("\n説明文生成中...")
    new_body = create_updated_description(issue['body'] or "", latest_comments)
    
    print("\nIssue 説明文更新中...")
    result = update_issue_description(new_body)
    
    if result:
        print("\n" + "=" * 60)
        print("OK 完了: Issue 説明文に最新コメントへのリンクを追加しました")
        print("=" * 60)
        print(f"\nIssue URL: {result['html_url']}")
        print(f"最新コメント直接URL: {latest_comments[0]['html_url']}")
    else:
        print("\nNG Issue 説明文更新に失敗しました")

if __name__ == '__main__':
    main()
