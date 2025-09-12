# ClaudeCode Remote Control Tools

GitHub Issue経由でClaudeCodeを遠隔操作するための統合システム

## 🎯 システム概要

2つの主要システムで構成:

### 1. SSスクリーンショットシステム
- GitHub Issue #1に「ss」とコメント → 自動スクリーンショット撮影・アップロード
- 10秒間隔でポーリング監視
- 10時間自動停止機能付き

### 2. ClaudeCode遠隔制御システム  
- GitHub Issue #1に「upper: メッセージ」→ Claude Code上部ペインに入力
- GitHub Issue #1に「lower: メッセージ」→ Claude Code下部ペインに入力  
- 30秒間隔でポーリング監視
- 全コメント検索（111+件対応）

## 📁 ファイル構成

```
remote-control-tools/
├── screenshot-system/
│   ├── real_time_monitor.py      # SSスクリーンショット監視システム
│   └── .env.template             # GitHub設定テンプレート
├── claude-control-system/
│   ├── gh_issue1_to_claude_paste.py  # Claude Code制御システム
│   ├── README.md                     # 詳細説明
│   └── requirements.txt              # Python依存関係
├── management-tools/
│   ├── start_github_remote.bat       # 統合起動スクリプト
│   ├── stop_github_remote.bat        # 統合停止スクリプト
│   ├── status_check.bat              # システム状態確認
│   └── README.md                     # 管理ツール説明
└── README.md                         # このファイル
```

## ⚙️ セットアップ

### 1. 依存関係インストール
```bash
cd remote-control-tools/claude-control-system
pip install -r requirements.txt
```

### 2. GitHub設定
`.env.template`を`.env`にコピーして設定:
```env
GITHUB_TOKEN=ghp_your_personal_access_token
GITHUB_REPO=Tenormusica2024/web-remote-desktop
GITHUB_BRANCH=master
```

### 3. 環境変数設定（推奨）
```batch
set GITHUB_TOKEN=ghp_your_personal_access_token_here
```

### 4. システム起動
```bash
# 管理フォルダに移動
cd remote-control-tools/management-tools

# 両システム一括起動
start_github_remote.bat

# システム状態確認
status_check.bat

# 両システム停止
stop_github_remote.bat
```

## 🚀 使用方法

### GitHub Issue #1での操作
1. **スクリーンショット**: 「ss」とコメント
2. **上部ペイン入力**: 「upper: あなたのメッセージ」
3. **下部ペイン入力**: 「lower: あなたのメッセージ」

### システム動作確認
- **SSシステム**: 10秒間隔でポーリング、コメント検知で即座にスクリーンショット撮影
- **制御システム**: 30秒間隔でポーリング、GitHub API pagination対応で全コメント検索

## 🔧 技術詳細

### 主要修正点
- **GitHub API pagination実装**: 111+件のコメント全検索対応（従来30件制限を解決）
- **Unicode encoding対応**: Windows cp932エラー解消
- **状態管理最適化**: 重複処理防止とETAG活用
- **セキュリティ強化**: 環境変数トークン対応
- **10時間自動停止**: SSシステムの長時間実行制限

### システム要件
- Python 3.x
- Windows環境（BAT管理ツール）
- PyAutoGUI, PyPerClip対応
- GitHub Personal Access Token

## 📊 パフォーマンス

- **SSシステム**: 10秒ポーリング、レスポンス時間 < 5秒
- **制御システム**: 30秒ポーリング、即座にClaude Codeペイン入力
- **GitHub API効率**: ETagキャッシュ + pagination で最適化

## 🛡️ セキュリティ

- **環境変数トークン**: ハードコード回避
- Personal Access Token最小権限（Issues, Contents）
- プライベートリポジトリ使用推奨
- ログファイル機密情報フィルタリング

## 📝 ログとモニタリング

- `logs/issue1_monitor_YYYYMMDD.log` - 制御システムログ
- `realtime_monitor.log` - SSシステムログ
- JSON状態ファイルによる継続性確保

## 🔄 アップデート履歴

### v1.1 (2025-09-12)
- **セキュリティ強化**: 環境変数GITHUB_TOKEN対応
- **Push Protection対応**: ハードコードトークン除去
- **警告システム**: トークン未設定時の警告表示

### v1.0 (Initial Release)
- GitHub Issue #1完全対応
- SSスクリーンショット + Claude Code制御統合
- 111+コメント対応（GitHub API pagination）

---

*GitHub Issue remote control system for Claude Code - セキュリティ強化版*