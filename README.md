# ClaudeCode Remote Screenshot System

GitHub Issue 経由で遠隔スクリーンショット指示システム

## 🎯 システム概要

- **社内PC** → GitHub Issue に「screenshot」コメント
- **自宅PC** → コメント検知 → 自動スクリーンショット撮影・アップロード
- **結果** → GitHub Issue に画像付きでレスポンス

## 📁 ファイル構成

```
cc-snap-to-github/
├── .env                       # 設定ファイル
├── requirements.txt           # Python依存関係
├── pc-snap-uploader.py       # 手動ホットキー版
├── remote-monitor.py         # 遠隔監視サービス (メイン)
├── send-screenshot-command.py # 社内PC用指示送信
├── start_uploader.bat        # 手動版起動
├── start-remote-monitor.bat  # 遠隔監視開始
├── request-screenshot.bat    # 社内PC用(簡単操作)
└── README.md                 # このファイル
```

## ⚙️ セットアップ手順

### 1. GitHub設定

1. **プライベートリポ作成** (例: `your-org/ops-screenshots`)
2. **Issue作成** (例: #1 "Remote Screenshot Commands")
3. **Personal Access Token作成**
   - Repository permissions → Contents: Read/Write, Issues: Read/Write

### 2. 自宅PC設定

`.env` ファイルを編集：

```env
# 必須設定
GITHUB_TOKEN=ghp_your_personal_access_token_here
GITHUB_REPO=your-org/ops-screenshots
GITHUB_BRANCH=main

# 遠隔監視設定
MONITOR_ISSUE_NUMBER=1        # 監視するIssue番号
POLL_INTERVAL=30              # チェック間隔(秒)
```

### 3. 依存関係インストール

```bash
pip install -r requirements.txt
```

## 🚀 使用方法

### 自宅PC（監視サイド）

**監視サービス開始：**
```bash
# バックグラウンド監視開始
.\start-remote-monitor.bat

# または直接実行
python remote-monitor.py
```

**ログ確認：**
```bash
# ログファイル確認
type monitor.log

# リアルタイム監視
Get-Content monitor.log -Wait
```

### 社内PC（指示サイド）

**方法1: 環境変数設定 + バッチ実行**
```cmd
set GITHUB_TOKEN=ghp_your_token_here
set GITHUB_REPO=your-org/ops-screenshots
set MONITOR_ISSUE_NUMBER=1

.\request-screenshot.bat
```

**方法2: Python直接実行**
```bash
python send-screenshot-command.py
python send-screenshot-command.py --urgent
python send-screenshot-command.py --note "Claude Code stuck"
```

**方法3: GitHub Web UI直接**
- Issue #1 に「screenshot」とコメント投稿

## 🔍 動作フロー

```
[社内PC] "screenshot" コメント投稿
    ↓
[GitHub Issue] 新しいコメント
    ↓  
[自宅PC] 30秒間隔でポーリング検知
    ↓
[自宅PC] スクリーンショット撮影
    ↓
[GitHub] screenshots/YYYY/MM/ にアップロード
    ↓
[GitHub Issue] 結果を画像付きコメントで報告
```

## 🎛️ 高度な使用方法

### コマンドバリエーション

- `screenshot` - 通常のスクリーンショット
- `スクショ` - 日本語でも可
- `🚨 URGENT: screenshot` - 緊急フラグ付き
- `screenshot Claude Code stuck` - 備考付き

### 監視サービス管理

```bash
# 一度だけチェック（テスト用）
python remote-monitor.py --once

# テストスクリーンショット
python remote-monitor.py --test

# ログレベル調整（環境変数）
set LOG_LEVEL=DEBUG
```

### 複数Issue対応

監視対象を増やす場合は `MONITOR_ISSUE_NUMBER` に複数設定：

```python
# remote-monitor.py を編集してカスタマイズ可能
MONITOR_ISSUES = ["1", "5", "10"]  # 複数Issue監視
```

## 🛡️ セキュリティ考慮事項

- **PAT権限**: 必要最小限（Contents:RW, Issues:RW）に限定
- **プライベートリポ**: 画像を外部公開しない
- **監視ログ**: 機密情報をログ出力しない設定済み
- **プロキシ対応**: 社内環境のHTTP(S)_PROXYを自動認識

## 🔧 トラブルシューティング

### よくある問題

1. **監視が動かない**
   ```bash
   python remote-monitor.py --once  # 手動テスト
   ```

2. **GitHub API エラー**
   - PAT の権限確認
   - レート制限（5000 req/h）確認

3. **スクリーンショットが撮れない**
   ```bash
   python remote-monitor.py --test  # 撮影テスト
   ```

4. **社内PC から指示が届かない**
   - Issue 番号の確認
   - GITHUB_REPO の設定確認

### ログ分析

```bash
# エラーのみ抽出
findstr "ERROR" monitor.log

# 今日のアクティビティ
findstr "2024-01-15" monitor.log
```

## 📊 運用Tips

- **定期監視**: タスクスケジューラで自動起動
- **複数PC**: 同じ設定で複数の自宅PCから並行監視可能  
- **通知設定**: 重要Issue には Slack/Discord 通知連携
- **バックアップ**: 重要なスクショは定期的に別ストレージへ

## 🎯 応用例

- **ClaudeCode 応答監視**: プロセス監視と組み合わせて自動検知
- **定期ヘルスチェック**: cron で定時スクリーンショット
- **複数画面対応**: 特定モニタのみ撮影設定
- **動画録画**: 連続スクリーンショットで簡易動画生成