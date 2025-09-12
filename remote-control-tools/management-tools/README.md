# GitHub統合リモート制御システム 管理フォルダ

> **独立管理フォルダ**: `C:\Users\Tenormusica\GitHub-Remote-Control-Manager`

## 📋 概要

GitHub Issue #1を通じたリモートデスクトップ制御システムの統合管理バッチファイル集

### 🎯 システム構成

1. **SSスクリーンショット投稿システム**
   - **機能**: GitHubコメント「ss」を検知して自動スクリーンショット投稿
   - **監視間隔**: 10秒
   - **自動停止**: 10時間後
   - **場所**: `C:\Users\Tenormusica\Documents\github-remote-desktop\`

2. **Claude Codeリモート制御システム**
   - **機能**: 「upper:/lower: メッセージ」を検知してClaude Codeに自動入力
   - **監視間隔**: 30秒  
   - **継続監視**: 無制限
   - **場所**: `C:\Users\Tenormusica\cc-snap-to-github\`

## 🛠️ 管理バッチファイル

| ファイル名 | 機能 | 説明 |
|-----------|------|------|
| `start_github_remote.bat` | 🚀 統合起動 | 両システムを同時起動 |
| `stop_github_remote.bat` | 🛑 統合停止 | 全関連プロセスを安全停止 |
| `status_check.bat` | 📊 状態確認 | システム稼働状況確認 |

## ⚡ 実行方法

### コマンドライン実行
```batch
# 起動
"C:\Users\Tenormusica\GitHub-Remote-Control-Manager\start_github_remote.bat"

# 停止  
"C:\Users\Tenormusica\GitHub-Remote-Control-Manager\stop_github_remote.bat"

# 状態確認
"C:\Users\Tenormusica\GitHub-Remote-Control-Manager\status_check.bat"
```

### エクスプローラー実行
- フォルダを開いて各BATファイルをダブルクリック

## 📝 使用方法

### GitHubリモート制御
1. **スクリーンショット取得**: GitHub Issue #1に「ss」とコメント
2. **上部ペイン入力**: 「upper: メッセージ」とコメント  
3. **下部ペイン入力**: 「lower: メッセージ」とコメント

### システム管理
- **起動前確認**: `status_check.bat`で稼働状況確認
- **安全起動**: `start_github_remote.bat`で両システム起動
- **完全停止**: `stop_github_remote.bat`で全プロセス停止

## 🔍 トラブルシューティング

### プロセス確認
```cmd
# Python関連プロセス確認
wmic process where "name='python.exe'" get processid,commandline

# GitHub関連プロセス確認  
wmic process where "commandline like '%github%'" get processid,commandline
```

### ログファイル
- **SSシステム**: `C:\Users\Tenormusica\Documents\github-remote-desktop\realtime_monitor.log`
- **リモート制御**: Console出力（ステートファイル: `.gh_issue1_to_claude_state.json`）

### 手動プロセス停止
```cmd
# 特定プロセス停止
wmic process where "commandline like '%real_time_monitor%'" delete
wmic process where "commandline like '%gh_issue1_to_claude%'" delete
```

## 📊 システム要件

- **OS**: Windows 10/11
- **Python**: 3.7+
- **GitHub PAT**: 設定済み（Fine-grained Token）
- **依存パッケージ**: requests, pyautogui, pyperclip

## 🔐 セキュリティ

- **GitHub Token**: ハードコード（プロダクション環境では環境変数推奨）
- **プロセス管理**: wmic使用（管理者権限推奨）
- **自動停止**: SSシステムは10時間で自動停止

---

**作成日**: 2025-09-12  
**最終更新**: 2025-09-12  
**バージョン**: 1.0  
**作成者**: Claude Code Assistant