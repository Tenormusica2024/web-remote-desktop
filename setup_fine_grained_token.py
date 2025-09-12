#!/usr/bin/env python3
"""
Fine-grained Personal Access Token Setup Script
GitHub Fine-grained tokenの設定専用スクリプト
"""

import os
from pathlib import Path

def setup_fine_grained_token():
    """Fine-grained Personal Access Tokenの設定"""
    
    root = Path(__file__).resolve().parent
    env_file = root / ".env"
    
    print("=== Fine-grained Personal Access Token Setup ===")
    print("Fine-grained tokenは特定のリポジトリに限定された権限を持つトークンです。")
    print()
    print("必要な権限:")
    print("- Repository access: 対象リポジトリ (Tenormusica2024/web-remote-desktop)")
    print("- Repository permissions:")
    print("  - Contents: Read and Write (スクリーンショットファイルのアップロード用)")
    print("  - Issues: Read and Write (Issue監視・コメント投稿用)")
    print("  - Metadata: Read (リポジトリ情報取得用)")
    print()
    print("トークンをペーストしてください (gho_/ghu_/ghs_で始まるはずです):")
    
    new_token = input("Fine-grained Token: ").strip()
    
    if not new_token:
        print("❌ トークンが入力されていません。終了します。")
        return False
    
    # Fine-grained tokenの形式チェック
    if not new_token.startswith(('gho_', 'ghu_', 'ghs_')):
        print("⚠️ Warning: Fine-grained tokenは通常 gho_/ghu_/ghs_ で始まります")
        print("入力されたトークン:", new_token[:10] + "...")
        confirm = input("本当にこのトークンを使用しますか? (y/N): ").strip().lower()
        if confirm != 'y':
            print("セットアップをキャンセルしました。")
            return False
    
    try:
        # .envファイル更新
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # トークン行を置換
        lines = content.split('\n')
        updated_lines = []
        token_updated = False
        
        for line in lines:
            if line.startswith('GITHUB_TOKEN='):
                updated_lines.append(f'GITHUB_TOKEN={new_token}')
                print("✅ Fine-grained tokenを.envファイルに設定しました")
                token_updated = True
            else:
                updated_lines.append(line)
        
        if not token_updated:
            # GITHUB_TOKEN行が存在しない場合は追加
            updated_lines.append(f'GITHUB_TOKEN={new_token}')
            print("✅ Fine-grained tokenを.envファイルに追加しました")
        
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(updated_lines))
        
        print("✅ 設定が完了しました!")
        print()
        print("次のステップ:")
        print("1. テスト実行: python test_github_access.py")
        print("2. 動作確認: python remote-monitor.py --test")
        print("3. 監視開始: python remote-monitor.py")
        print()
        print("Fine-grained tokenの権限が正しく設定されていることを確認してください:")
        print("- Repository access: Tenormusica2024/web-remote-desktop")
        print("- Contents: Read and Write")
        print("- Issues: Read and Write") 
        print("- Metadata: Read")
        
        return True
        
    except Exception as e:
        print(f"❌ 設定中にエラーが発生しました: {e}")
        return False

if __name__ == "__main__":
    setup_fine_grained_token()