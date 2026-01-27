#!/usr/bin/env python3
"""
GitHub Issue #5 の古いコメントを1000件削除するスクリプト
100件ずつ取得→削除を繰り返す方式
"""
import subprocess
import json
import time
import os
import sys

OWNER = "Tenormusica2024"
REPO = "Private"
ISSUE_NUMBER = 5
DELETE_COUNT = 1000
BATCH_SIZE = 100

def get_clean_env():
    """GITHUB_TOKENを除いた環境変数を返す"""
    env = os.environ.copy()
    env.pop('GITHUB_TOKEN', None)
    env.pop('GH_TOKEN', None)
    return env

def get_comments_batch():
    """コメントを100件取得（古い順）"""
    cmd = [
        "C:\\Program Files\\GitHub CLI\\gh.exe", "api",
        f"repos/{OWNER}/{REPO}/issues/{ISSUE_NUMBER}/comments?per_page={BATCH_SIZE}&sort=created&direction=asc"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', env=get_clean_env())
    if result.returncode != 0:
        print(f"Error: {result.stderr}", flush=True)
        return []
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return []

def delete_comment(comment_id):
    """コメントを削除 - 正しいエンドポイント使用"""
    cmd = [
        "C:\\Program Files\\GitHub CLI\\gh.exe", "api",
        "-X", "DELETE",
        f"repos/{OWNER}/{REPO}/issues/comments/{comment_id}"  # issue番号は不要
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', env=get_clean_env())
    return result.returncode == 0

def main():
    print(f"=== GitHub Issue #{ISSUE_NUMBER} コメント削除開始 ===", flush=True)
    print(f"対象: {OWNER}/{REPO}", flush=True)
    print(f"目標削除数: {DELETE_COUNT}件（古い順）", flush=True)
    print(f"バッチサイズ: {BATCH_SIZE}件", flush=True)
    print(flush=True)

    total_deleted = 0
    total_errors = 0
    batch_count = 0

    while total_deleted < DELETE_COUNT:
        batch_count += 1
        print(f"--- バッチ {batch_count}: コメント取得中... ---", flush=True)

        comments = get_comments_batch()
        if not comments:
            print("これ以上コメントがありません", flush=True)
            break

        batch_deleted = 0
        batch_errors = 0

        for comment in comments:
            if total_deleted >= DELETE_COUNT:
                break

            comment_id = comment["id"]
            if delete_comment(comment_id):
                batch_deleted += 1
                total_deleted += 1
            else:
                batch_errors += 1
                total_errors += 1

        print(f"バッチ {batch_count}: {batch_deleted}件削除 (累計: {total_deleted}件)", flush=True)

        # レートリミット対策
        if total_deleted < DELETE_COUNT:
            time.sleep(1)

    print(flush=True)
    print("=== 削除完了 ===", flush=True)
    print(f"削除成功: {total_deleted}件", flush=True)
    print(f"削除失敗: {total_errors}件", flush=True)

if __name__ == "__main__":
    main()
