# ClaudeCode Remote Desktop & Task Reporting System

GitHub Issue 経由で遠隔スクリーンショット指示 + Claude Code タスク自動報告システム

## 🎯 システム概要

### 1. 遠隔スクリーンショット機能
- **社内PC** → GitHub Issue に「screenshot」コメント
- **自宅PC** → コメント検知 → 自動スクリーンショット撮影・アップロード
- **結果** → GitHub Issue に画像付きでレスポンス

### 2. Claude Code タスク自動報告機能 (NEW)
- **Claude Code** → タスク完了・質問・エラー時に自動報告
- **GitHub Issue** → すべての状態変更がリアルタイムで記録
- **報告漏れ防止** → Skills + Hooks + CLAUDE.md の3層構造で強制

## 📁 ファイル構成

```
github-remote-desktop/
├── .env                       # 設定ファイル
├── .env_private               # プライベートリポジトリ用設定
├── requirements.txt           # Python依存関係
│
├── # 遠隔スクリーンショット機能
├── pc-snap-uploader.py       # 手動ホットキー版
├── remote-monitor.py         # 遠隔監視サービス (メイン)
├── send-screenshot-command.py # 社内PC用指示送信
├── start_uploader.bat        # 手動版起動
├── start-remote-monitor.bat  # 遠隔監視開始
├── request-screenshot.bat    # 社内PC用(簡単操作)
│
├── # タスク報告機能
├── task_complete_private.py  # GitHub Issue報告スクリプト
├── task_complete_private.bat # バッチ起動用
│
├── # Claude Code Skills & Hooks (NEW)
├── .claude/
│   ├── skills/
│   │   └── github-issue-reporter/
│   │       ├── SKILL.md      # スキル定義（必須実行条件）
│   │       ├── reference.md  # 詳細リファレンス
│   │       └── examples.md   # 使用例（5パターン）
│   └── hooks/
│       └── github-issue-reporter.ps1  # セッション終了時Hook
│
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

---

## 🤖 Claude Code タスク自動報告システム

### 概要

Claude Codeのすべての重要なアクション（タスク完了、質問、エラー、待機など）をGitHub Issueに自動報告するシステム。
従来のプロンプト方式では報告漏れが頻発していたため、**Skills + Hooks + CLAUDE.md の3層構造**で強制ルール化。

### アーキテクチャ

```
┌─────────────────────────────────────────────────────────────┐
│                     3層報告強制システム                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Layer 1: Skills (.claude/skills/github-issue-reporter/)   │
│  ├── Claude Codeが自動認識するルール定義                      │
│  ├── 必須実行トリガー6パターン                                │
│  └── ZERO TOLERANCEポリシー                                 │
│                                                             │
│  Layer 2: Hooks (~/.claude/settings.json)                  │
│  ├── Stop: セッション終了時に通知                            │
│  └── SubagentStop: サブエージェント終了時に通知              │
│                                                             │
│  Layer 3: CLAUDE.md (プロジェクトルール)                     │
│  ├── 毎回参照される強制ルール                                 │
│  ├── Skillsへの参照リンク                                    │
│  └── 必須実行タイミング定義                                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                          ↓
              GitHub Issue #5 (Private)
                  自動報告投稿
```

### 必須報告タイミング（6パターン）

| 状況 | 説明 | 報告内容例 |
|------|------|-----------|
| **完了** | タスクが正常に完了した時 | 実施内容、変更ファイル、コミット情報 |
| **質問** | ユーザーに確認が必要な時 | 質問内容、理由、選択肢 |
| **エラー** | 処理中にエラーが発生した時 | エラー詳細、試みた解決策、推奨アクション |
| **待機** | 追加入力を待つ時 | 待機理由、必要な情報 |
| **中断** | 作業を停止する時 | 中断理由、現在の状況 |
| **情報** | 分析・調査結果を報告する時 | 発見事項、推奨事項 |

### 使用方法

#### 手動報告（Claude Code内で実行）

```bash
cd "C:\Users\Tenormusica\Documents\github-remote-desktop" && python task_complete_private.py "[報告内容]"
```

#### 報告フォーマット（マークダウン必須）

```markdown
## タスク完了: [タイトル]

### 実施内容
- 項目1
- 項目2

### 変更ファイル
- `file1.py` - 説明
- `file2.js` - 説明

### 結果
[結果の詳細]
```

### Skillsファイル詳細

#### SKILL.md
スキル定義ファイル。Claude Codeが自動的に認識し、報告ルールを適用。

```yaml
---
name: github-issue-reporter
description: |
  GitHub Issue報告の自動実行スキル。タスク完了時、確認・質問時、
  エラー発生時、待機時に必ずGitHub Issueへ報告する。
allowed-tools: Bash, Read
---
```

#### reference.md
詳細リファレンス。全シナリオの報告内容・フォーマット・禁止事項を定義。

#### examples.md
5パターンの具体的な使用例（完了、質問、エラー、待機、情報提供）。

### Hooks設定

`~/.claude/settings.json` に以下を追加:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "powershell -ExecutionPolicy Bypass -File \"C:\\Users\\Tenormusica\\Documents\\github-remote-desktop\\.claude\\hooks\\github-issue-reporter.ps1\" -Context \"Stop\""
          }
        ]
      }
    ],
    "SubagentStop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "powershell -ExecutionPolicy Bypass -File \"C:\\Users\\Tenormusica\\Documents\\github-remote-desktop\\.claude\\hooks\\github-issue-reporter.ps1\" -Context \"SubagentStop\""
          }
        ]
      }
    ]
  }
}
```

### ZERO TOLERANCE ポリシー

以下は**完全禁止**:

- 「後で報告する」→ 禁止
- 「まとめて報告する」→ 禁止
- 「報告しなくてもいいだろう」→ 禁止
- 「質問だから報告不要」→ 禁止
- 「エラーだから報告しない」→ 禁止

### トラブルシューティング

#### 報告が失敗する場合

1. **ネットワークエラー**: 再試行する
2. **認証エラー**: `.env_private` の GITHUB_TOKEN を確認
3. **タイムアウト**: 報告内容を短くして再試行

#### Hooks動作確認

```bash
# ログファイル確認
type logs\hook_execution.log

# 手動テスト
powershell -ExecutionPolicy Bypass -File ".claude\hooks\github-issue-reporter.ps1" -Context "ManualTest"
```

### セットアップ手順

1. **Skillsのコピー**
   ```bash
   # グローバル設定にコピー
   xcopy /E /I ".claude\skills" "%USERPROFILE%\.claude\skills"
   ```

2. **settings.jsonの編集**
   - `~/.claude/settings.json` にHooks設定を追加

3. **CLAUDE.mdの確認**
   - `Task Completion Report Protocol` セクションが存在することを確認

4. **動作テスト**
   ```bash
   python task_complete_private.py "テスト報告"
   ```

### 更新履歴

| 日付 | バージョン | 変更内容 |
|------|-----------|---------|
| 2025-12-29 | v2.1.0 | PC起動時自動実行設定を追加 |
| 2025-12-25 | v2.0.0 | Skills & Hooks機能追加、3層報告強制システム実装 |
| 2025-09-xx | v1.0.0 | 初期リリース（遠隔スクリーンショット機能） |

---

## 🔄 PC起動時自動実行設定

### 概要

`private_issue_monitor_service.py` をPC起動時に自動的にバックグラウンドで実行する設定。

### 設定方法

1. **VBSファイルの配置**

以下の内容で VBS ファイルをスタートアップフォルダに配置：

**ファイルパス:** `C:\Users\Tenormusica\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\private_issue_monitor.vbs`

```vbs
Set objShell = CreateObject("WScript.Shell")
objShell.CurrentDirectory = "C:\Users\Tenormusica\Documents\github-remote-desktop"
objShell.Run "pythonw.exe private_issue_monitor_service.py", 0, False
```

2. **動作確認**

```bash
# プロセス確認
tasklist | findstr pythonw

# 手動起動テスト
wscript "C:\Users\Tenormusica\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\private_issue_monitor.vbs"
```

### 技術詳細

- **pythonw.exe**: コンソールウィンドウを表示しないPython実行ファイル
- **Run の第2引数 `0`**: ウィンドウを非表示で実行
- **Run の第3引数 `False`**: スクリプト終了を待たない（非同期実行）

### 停止方法

```bash
# プロセス終了
taskkill /f /im pythonw.exe
```

### トラブルシューティング

1. **起動しない場合**
   - Pythonのパスが通っているか確認
   - `pythonw.exe` が存在するか確認
   - VBSファイルのパスが正しいか確認

2. **エラー確認**
   - 手動でVBSファイルを実行してエラーを確認
   - `python private_issue_monitor_service.py` を直接実行してエラーを確認