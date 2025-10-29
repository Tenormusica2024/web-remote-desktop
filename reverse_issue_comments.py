#!/usr/bin/env python3
"""
GitHub Issue コメント表示順変更スクリプト
最新コメントが上に表示されるように設定を変更
"""

import os
import requests
import json

# GitHub APIトークンを環境変数から取得
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
if not GITHUB_TOKEN:
    print("エラー: GITHUB_TOKEN 環境変数が設定されていません")
    exit(1)

REPO_OWNER = "Tenormusica2024"
REPO_NAME = "Private"
ISSUE_NUMBER = 1

# GitHub API ヘッダー
headers = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}

def get_issue_comments():
    """Issue のすべてのコメントを取得"""
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/issues/{ISSUE_NUMBER}/comments"
    
    all_comments = []
    page = 1
    
    while True:
        params = {
            'per_page': 100,
            'page': page,
            'sort': 'created',
            'direction': 'desc'  # 降順（最新が先）
        }
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            print(f"エラー: API呼び出し失敗 (Status: {response.status_code})")
            print(response.text)
            return None
        
        comments = response.json()
        
        if not comments:
            break
        
        all_comments.extend(comments)
        page += 1
        
        print(f"取得: {len(comments)} コメント (ページ {page-1})")
    
    return all_comments

def create_summary_comment(total_comments):
    """最新コメントへのナビゲーション用サマリーコメントを作成"""
    
    summary_text = f"""# 📌 最新コメントへのクイックナビゲーション

**総コメント数**: {total_comments}

## 最新コメントを見るには

### 方法1: URL直接アクセス（最速）
最新のコメントURLを直接開く:
- ブラウザのURLバーに `#issuecomment-[最新ID]` を追加

### 方法2: ブラウザ検索機能
1. Ctrl+F で検索を開く
2. 最新の日付（例: "2025-10-02"）を検索
3. 下向き矢印で最新まで移動

### 方法3: GitHub CLI（ターミナル）
```bash
gh issue view 1 --repo Tenormusica2024/Private --comments | tail -50
```

### 方法4: APIで最新10件取得
```bash
curl -H "Authorization: token YOUR_TOKEN" \\
  "https://api.github.com/repos/Tenormusica2024/Private/issues/1/comments?per_page=10&sort=created&direction=desc"
```

---

**注意**: GitHubのIssue UI仕様上、コメント表示順は古い順が固定されており、設定で変更できません。
上記の回避策を使用して最新コメントに素早くアクセスしてください。

最終更新: {import datetime; datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    return summary_text

def post_summary_comment(summary_text):
    """サマリーコメントを Issue に投稿"""
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/issues/{ISSUE_NUMBER}/comments"
    
    data = {
        'body': summary_text
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 201:
        comment_data = response.json()
        print(f"✅ サマリーコメント投稿成功")
        print(f"URL: {comment_data['html_url']}")
        return comment_data
    else:
        print(f"❌ サマリーコメント投稿失敗 (Status: {response.status_code})")
        print(response.text)
        return None

def main():
    print("=" * 60)
    print("GitHub Issue コメント表示順変更スクリプト")
    print("=" * 60)
    
    # コメント一覧取得
    print("\n📥 コメント取得中...")
    comments = get_issue_comments()
    
    if comments is None:
        print("❌ コメント取得失敗")
        return
    
    print(f"\n✅ 総コメント数: {len(comments)}")
    
    # 最新コメント情報表示
    if comments:
        latest = comments[0]
        print(f"\n📌 最新コメント情報:")
        print(f"  ID: {latest['id']}")
        print(f"  作成日時: {latest['created_at']}")
        print(f"  URL: {latest['html_url']}")
        print(f"  投稿者: {latest['user']['login']}")
    
    # サマリーコメント作成・投稿
    print("\n📝 ナビゲーション用サマリーコメント作成中...")
    summary = create_summary_comment(len(comments))
    
    print("\n📤 サマリーコメント投稿中...")
    result = post_summary_comment(summary)
    
    if result:
        print("\n" + "=" * 60)
        print("✅ 完了: 最新コメントへのナビゲーションガイドを投稿しました")
        print("=" * 60)
        print(f"\nサマリーURL: {result['html_url']}")
        print(f"最新コメント直接URL: {comments[0]['html_url']}")
    else:
        print("\n❌ サマリーコメント投稿に失敗しました")

if __name__ == '__main__':
    main()
