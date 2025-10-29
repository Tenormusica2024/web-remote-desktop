#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys, time, json
from pathlib import Path
import requests

# .env_privateファイルの読み込み
env_file = Path(".env_private")
if env_file.exists():
    print(f"[OK] 設定ファイル読み込み: {env_file}")
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value
else:
    print(f"[NG] 設定ファイルが見つかりません: {env_file}")
    sys.exit(1)

# 設定値取得
GH_REPO = os.getenv("GH_REPO")
GH_ISSUE = os.getenv("GH_ISSUE") 
GH_TOKEN = os.getenv("GH_TOKEN")

print(f"[設定] Repository: {GH_REPO}")
print(f"[設定] Issue: #{GH_ISSUE}")
print(f"[設定] Token: {'あり' if GH_TOKEN else 'なし'}")

if not (GH_REPO and GH_ISSUE and GH_TOKEN):
    print("[エラー] 必要な設定が不足しています")
    sys.exit(1)

# セッション作成
session = requests.Session()
session.headers.update({
    "Authorization": f"Bearer {GH_TOKEN}",
    "Accept": "application/vnd.github+json",
    "User-Agent": "private-test/1.0"
})

# APIテスト
comments_url = f"https://api.github.com/repos/{GH_REPO}/issues/{GH_ISSUE}/comments"
print(f"[テスト] API URL: {comments_url}")

try:
    r = session.get(comments_url, timeout=10)
    print(f"[結果] ステータス: {r.status_code}")
    
    if r.status_code == 200:
        comments = r.json()
        print(f"[結果] コメント数: {len(comments)}")
        
        # 状態ファイルテスト
        state_file = Path(".gh_issue_to_claude_state_private_new.json")
        state = {"last_comment_id": 0, "comments_etag": None}
        
        if state_file.exists():
            print(f"[状態] 既存状態ファイル読み込み")
            state = json.loads(state_file.read_text(encoding="utf-8"))
        else:
            print(f"[状態] 新規状態ファイル作成")
        
        last_id = state.get("last_comment_id", 0)
        print(f"[状態] 最後のコメントID: {last_id}")
        
        # 新しいコメント検索
        to_process = [c for c in comments if c.get("id", 0) > last_id]
        print(f"[処理] 新規コメント数: {len(to_process)}")
        
        if to_process:
            for c in to_process:
                cid = c.get("id", 0)
                user = (c.get("user") or {}).get("login", "")
                body = c.get("body", "").replace('\n', ' ')[:50]
                print(f"  - ID: {cid}, User: {user}, Body: {body}...")
        else:
            print("  - 新規コメントはありません")
            
        # 状態保存
        if comments:
            latest_id = max(c.get("id", 0) for c in comments)
            state["last_comment_id"] = latest_id
            state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
            print(f"[保存] 最新コメントID {latest_id} を状態ファイルに保存")
            
    else:
        print(f"[エラー] APIエラー: {r.text[:100]}")
        
except Exception as e:
    print(f"[例外] {e.__class__.__name__}: {e}")

print("[完了] テスト終了")