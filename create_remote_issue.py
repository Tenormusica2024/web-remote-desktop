#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Claude Code Remote Control Issue作成スクリプト
"""

import requests
import json

# GitHub設定
GITHUB_TOKEN = "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"
GITHUB_REPO = "Tenormusica2024/web-remote-desktop"
API_BASE = "https://api.github.com"

session = requests.Session()
session.headers.update({
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
})

def create_remote_control_issue():
    """Claude Code Remote Control用のIssueを作成"""
    owner, repo = GITHUB_REPO.split("/", 1)
    url = f"{API_BASE}/repos/{owner}/{repo}/issues"
    
    title = "Claude Code Remote Control Commands"
    body = """# Claude Code リモート制御コマンド

このIssueは、GitHub Issue to Claude Code システム用の制御Issueです。

## 使用方法

コメントにテキストを投稿すると、自動的にClaude Codeの入力欄に送信されます。

### コメント書式

- `upper: メッセージ` → 右上ペインに送信
- `lower: メッセージ` → 右下ペインに送信  
- プレフィックスなし → 下部ペインに送信（デフォルト）

### 使用例

```
upper: YouTubeの文字起こしツールについて教えて
```

```  
lower: プログラムのバグを修正してください
```

```
Claude Codeの使い方を教えて（下部ペインに送信）
```

## システム情報

- 監視間隔: 5秒
- 対象ユーザー: Tenormusica2024（他のユーザーのコメントは無視）
- 自動実行: コメント投稿後、自動的にEnterキーが押されます

---

*このIssueは自動監視されています。システムが動作中の場合、コメントが即座にClaude Codeに送信されます。*"""

    payload = {
        "title": title,
        "body": body,
        "labels": ["automation", "remote-control"]
    }
    
    try:
        r = session.post(url, json=payload, timeout=30)
        if r.status_code == 201:
            issue_data = r.json()
            try:
                print("✅ Claude Code Remote Control Issue作成成功！")
                print(f"   Issue番号: #{issue_data['number']}")
                print(f"   URL: {issue_data['html_url']}")
            except UnicodeEncodeError:
                print("OK Claude Code Remote Control Issue created successfully!")
                print(f"   Issue number: #{issue_data['number']}")
                print(f"   URL: {issue_data['html_url']}")
            return issue_data['number']
        else:
            try:
                print(f"❌ Issue作成失敗: {r.status_code}")
                print(f"   エラー内容: {r.text}")
            except UnicodeEncodeError:
                print(f"NG Issue creation failed: {r.status_code}")
                print(f"   Error: {r.text}")
            return None
    except Exception as e:
        try:
            print(f"❌ エラー: {e}")
        except UnicodeEncodeError:
            print(f"NG Error: {e}")
        return None

if __name__ == "__main__":
    try:
        print("Claude Code Remote Control Issue を作成しています...")
    except UnicodeEncodeError:
        print("Creating Claude Code Remote Control Issue...")
    
    issue_number = create_remote_control_issue()
    
    if issue_number:
        try:
            print(f"\n次の手順:")
            print(f"1. setup_claude_remote.bat を実行して環境を準備")
            print(f"2. python gh_issue_to_claude_paste.py --calibrate でキャリブレーション")
            print(f"3. python gh_issue_to_claude_paste.py でシステム開始")
            print(f"4. GitHub Issue #{issue_number} にコメントを投稿してテスト")
        except UnicodeEncodeError:
            print(f"\nNext steps:")
            print(f"1. Run setup_claude_remote.bat to prepare environment")
            print(f"2. python gh_issue_to_claude_paste.py --calibrate for calibration")
            print(f"3. python gh_issue_to_claude_paste.py to start system")
            print(f"4. Post comment to GitHub Issue #{issue_number} for testing")
    else:
        try:
            print("\nIssue作成に失敗しました。GitHubトークンと権限を確認してください。")
        except UnicodeEncodeError:
            print("\nIssue creation failed. Please check GitHub token and permissions.")