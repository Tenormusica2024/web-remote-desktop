# GitHub Issue ⇔ Claude Code 連携システム完全ドキュメント

## 📋 システム概要

本システムは、GitHub IssueとClaude Code間で双方向コメント転送・自動スクリーンショット撮影を実現する3つのPythonツールで構成されています。

## 🎯 システム構成

### 1. private_issue_monitor_service.py

**役割**: GitHub Issue → Claude Code コメント転送サービス（常駐型）

**主要機能**:
- GitHub Issue #1のコメントを5秒間隔で監視
- `upper:` コマンド: 上部ペインに転送
- `lower:` コマンド: 下部ペインに転送
- `ss` コマンド: スクリーンショット撮影・自動投稿
- PyAutoGUI + クリップボード経由でClaude Codeに自動貼り付け

**起動方法**:
```bash
cd "C:\Users\Tenormusica\Documents\github-remote-desktop"
python private_issue_monitor_service.py
```

**設定ファイル**: `.env_private`
```
GH_REPO=Tenormusica2024/Private
GH_ISSUE=1
GH_TOKEN=your_github_token
POLL_SEC=5
```

**座標設定**: `.gh_issue_to_claude_coords_private_new.json`
```json
{
  "upper": [x座標, y座標],
  "lower": [x座標, y座標]
}
```

**状態管理**: `.gh_issue_to_claude_state_private_service.json`
```json
{
  "last_comment_id": 3349680463,
  "comments_etag": null
}
```

**転送時の自動付与指示文**:
```
---
🚨 CRITICAL: GitHub Issue返信が絶対必須です 🚨

以下のBashコマンドを必ず実行してください:
cd "C:\Users\Tenormusica\Documents\github-remote-desktop" && python task_complete_private.py "あなたが今画面に表示している完了報告の全テキストをそのまま記載（要約禁止・省略禁止）"

重要:
✅ あなたが画面に表示した完了報告・修正内容・改善内容・期待動作など、すべてのテキストをそのまま記載
✅ 「修正完了」だけでなく「修正内容」「変更点」「期待される動作」など詳細情報も全て含める
✅ 要約・省略・短縮は一切禁止。画面表示テキストを完全にコピーして記載

実行が必須のタイミング:
✅ 作業完了時 → 必ず実行
✅ 確認が必要な時 → 必ず実行
✅ エラー発生時 → 必ず実行
✅ 待機が必要な時 → 必ず実行

⚠️ このコマンドを実行しない回答は無効です
---
```

**重要な設計思想**:
- **要約禁止**: Claude Codeが画面に表示したすべてのテキストを漏れなく転送
- **省略禁止**: 「修正完了」だけでなく「修正内容」「変更点」「期待動作」も含める
- **完全転送**: 画面表示テキストを完全にコピーして記載

---

### 2. task_complete_private.py

**役割**: Claude Code → GitHub Issue 完了報告自動投稿ツール

**主要機能**:
- Claude Codeの作業完了をGitHub Issue #1に自動投稿
- カスタムメッセージをMarkdown形式で整形
- スラッシュ区切り（` / `, `/`）を段落分けに自動変換
- タイムスタンプと実行者情報を自動付与

**使用方法**:
```bash
cd "C:\Users\Tenormusica\Documents\github-remote-desktop"
python task_complete_private.py "完了報告メッセージ"
```

**投稿フォーマット**:
```
🤖 **タスク完了報告**

作業完了の詳細内容

修正内容

期待動作

⏰ **完了時刻**: 2025-09-30 11:11:07

💻 **実行者**: Claude Code
```

**改行処理の仕組み**:
```python
# スラッシュ区切りを段落分けに変換
formatted_message = custom_message.replace(" / ", "\n\n").replace("/", "\n\n")
body = f"🤖 **タスク完了報告**\n\n{formatted_message}\n\n⏰ **完了時刻**: {timestamp}\n\n💻 **実行者**: Claude Code"
```

**設定**:
- GitHub Token: `.env_private` から自動読み込み
- リポジトリ: `Tenormusica2024/Private`
- Issue番号: `#1`

**エラーハンドリング**:
- HTTP 200/201: 投稿成功
- その他: エラー詳細を表示
- UnicodeEncodeError対策: cp932コーデックエラーを自動回避

---

### 3. remote-monitor_private.py

**役割**: リモートスクリーンショット自動撮影サービス（10時間制限付き常駐型）

**主要機能**:
- GitHub Issue #1のコメントとタイトルを30秒間隔で監視
- `ss` コマンド検出時に自動スクリーンショット撮影
- 撮影画像をGitHub Repositoryにアップロード
- 結果をGitHub Issue #1にコメント投稿
- 重複実行防止機能（冷却期間60秒）
- 10時間後に自動停止

**起動方法**:
```bash
cd "C:\Users\Tenormusica\Documents\github-remote-desktop"
python remote-monitor_private.py
```

**コマンド**:
- コメントに `ss` を記載
- Issue タイトルを `ss` を含む内容に変更

**動作フロー**:
1. GitHub Issue監視
2. `ss` コマンド検出
3. PyAutoGUIでスクリーンショット撮影
4. GitHub API経由で画像アップロード（`screenshots/YYYY/MM/` フォルダ）
5. GitHub Issue #1にコメント投稿（画像URL付き）

**投稿フォーマット**:
```
✅ **Screenshot taken** (requested by @username)

📸 **File**: `screenshots/2025/10/screenshot_20251014_120000.png`

🔗 **URL**: https://raw.githubusercontent.com/Tenormusica2024/Private/master/screenshots/2025/10/screenshot_20251014_120000.png
```

**重複防止機能**:
- **冷却期間**: 60秒間の冷却期間を設定
- **処理済み追跡**: `processed_screenshot_comments` セットで管理
- **タイトル重複防止**: `last_title_content_private.txt` でタイトル内容を追跡
- **同一作者連続コメント**: 同じ作者の連続した同じ内容のコメントをスキップ

**自動停止機能**:
- 起動から10時間（36000秒）で自動停止
- 1時間ごとに残り時間をログ出力
- 長時間放置による不要なAPI消費を防止

**設定ファイル**: `.env_private`
```
GITHUB_TOKEN=your_github_token
GITHUB_REPO=Tenormusica2024/Private
GITHUB_BRANCH=master
MONITOR_ISSUE_NUMBER=1
POLL_INTERVAL=30
```

**状態管理**:
- `last_comment_id_private.txt`: 最後に処理したコメントID
- `last_title_content_private.txt`: 最後に処理したタイトル内容
- `monitor_private.log`: 実行ログ

---

## 🔄 システム連携フロー

### パターン1: GitHub Issue → Claude Code（コメント転送）

```
1. ユーザーがGitHub Issue #1にコメント投稿
   例: "lower: AI FM Podcastのエラーを修正してください"
   
2. private_issue_monitor_service.pyが検出
   
3. Claude Code下部ペインに自動貼り付け
   内容: 元のメッセージ + 自動付与指示文
   
4. Claude Codeが作業実行
```

### パターン2: Claude Code → GitHub Issue（完了報告）

```
1. Claude Codeが作業完了
   
2. 自動付与指示文に従いBashコマンド実行
   cd "C:\Users\Tenormusica\Documents\github-remote-desktop" && python task_complete_private.py "完了報告"
   
3. task_complete_private.pyがGitHub Issue #1にコメント投稿
   
4. ユーザーが確認
```

### パターン3: リモートスクリーンショット

```
1. ユーザーがGitHub Issue #1にコメント投稿
   例: "ss"
   
2. remote-monitor_private.pyが検出
   
3. PyAutoGUIでスクリーンショット撮影
   
4. GitHub Repositoryにアップロード
   
5. GitHub Issue #1に結果投稿（画像URL付き）
```

---

## 📝 使用例

### 例1: 下部ペインで作業実行

**GitHub Issue #1にコメント投稿**:
```
lower: podcast-cloud-appのデプロイエラーを修正してください。
エラー内容: HTTP 500 Internal Server Error
```

**Claude Code下部ペインに自動転送**:
```
podcast-cloud-appのデプロイエラーを修正してください。
エラー内容: HTTP 500 Internal Server Error

---
🚨 CRITICAL: GitHub Issue返信が絶対必須です 🚨
（以下略）
```

**Claude Codeが作業完了後**:
```bash
cd "C:\Users\Tenormusica\Documents\github-remote-desktop" && python task_complete_private.py "デプロイエラー修正完了 / 修正内容: app.pyの環境変数読み込み処理を修正 / 期待動作: HTTP 200でアクセス可能"
```

**GitHub Issue #1に投稿される内容**:
```
🤖 **タスク完了報告**

デプロイエラー修正完了

修正内容: app.pyの環境変数読み込み処理を修正

期待動作: HTTP 200でアクセス可能

⏰ **完了時刻**: 2025-10-14 12:00:00

💻 **実行者**: Claude Code
```

### 例2: スクリーンショット撮影

**GitHub Issue #1にコメント投稿**:
```
ss
```

**remote-monitor_private.py が検出**:
- スクリーンショット撮影
- GitHub Repositoryにアップロード
- GitHub Issue #1に結果投稿

**GitHub Issue #1に投稿される内容**:
```
✅ **Screenshot taken** (requested by @Tenormusica2024)

📸 **File**: `screenshots/2025/10/screenshot_20251014_120000.png`

🔗 **URL**: https://raw.githubusercontent.com/Tenormusica2024/Private/master/screenshots/2025/10/screenshot_20251014_120000.png
```

---

## ⚙️ セットアップ手順

### 1. 環境変数設定

**`.env_private` ファイル作成**:
```bash
cd C:\Users\Tenormusica\Documents\github-remote-desktop
notepad .env_private
```

**内容**:
```
GH_REPO=Tenormusica2024/Private
GH_ISSUE=1
GH_TOKEN=github_pat_XXXXXXXXXXXXXXXXXXXX
POLL_SEC=5

GITHUB_TOKEN=github_pat_XXXXXXXXXXXXXXXXXXXX
GITHUB_REPO=Tenormusica2024/Private
GITHUB_BRANCH=master
MONITOR_ISSUE_NUMBER=1
POLL_INTERVAL=30
```

### 2. 座標設定

**Claude Codeの入力欄座標を取得**:
1. Claude Codeを起動
2. 上部ペイン・下部ペインの入力欄にマウスカーソルを合わせる
3. 座標を記録

**`.gh_issue_to_claude_coords_private_new.json` ファイル作成**:
```json
{
  "upper": [800, 400],
  "lower": [800, 900]
}
```

### 3. サービス起動

**ターミナル1: private_issue_monitor_service.py**
```bash
cd "C:\Users\Tenormusica\Documents\github-remote-desktop"
python private_issue_monitor_service.py
```

**ターミナル2: remote-monitor_private.py**
```bash
cd "C:\Users\Tenormusica\Documents\github-remote-desktop"
python remote-monitor_private.py
```

### 4. 動作確認

**GitHub Issue #1にテストコメント投稿**:
```
lower: テスト
```

**Claude Code下部ペインに自動転送されることを確認**

**Claude Codeでコマンド実行**:
```bash
cd "C:\Users\Tenormusica\Documents\github-remote-desktop" && python task_complete_private.py "テスト完了"
```

**GitHub Issue #1にコメントが投稿されることを確認**

---

## 🔧 トラブルシューティング

### 問題1: コメントが転送されない

**原因**:
- GitHub Token権限不足
- ポーリング間隔が長すぎる
- 座標設定が間違っている

**対処**:
1. GitHub Tokenの権限確認（repo, issuesスコープが必要）
2. `POLL_SEC`を短く設定（推奨: 5秒）
3. 座標を再設定

### 問題2: 完了報告が投稿されない

**原因**:
- task_complete_private.pyのパスが間違っている
- GitHub Token権限不足
- コマンド実行漏れ

**対処**:
1. フルパスで実行: `cd "C:\Users\Tenormusica\Documents\github-remote-desktop" && python task_complete_private.py "メッセージ"`
2. GitHub Tokenの権限確認
3. 自動付与指示文を確認（CRITICAL警告が表示されているか）

### 問題3: スクリーンショットが撮影されない

**原因**:
- PyAutoGUIが画面をキャプチャできない
- 重複防止機能で冷却期間中
- GitHub APIエラー

**対処**:
1. PyAutoGUIの動作確認: `python -c "import pyautogui; pyautogui.screenshot()"`
2. 60秒待機してから再実行
3. ログファイル確認: `monitor_private.log`

### 問題4: 改行が正しく表示されない

**原因**:
- GitHub Markdownの改行ルール（`\n\n`が必要）
- スラッシュ区切りが変換されていない

**対処**:
1. task_complete_private.pyのformatted_message変換処理を確認
2. スラッシュ区切り（` / `, `/`）を使用
3. 例: `"内容1 / 内容2 / 内容3"`

---

## 📊 システム設計思想

### 1. 完全自動化
- ユーザーはGitHub Issueにコメントするだけ
- Claude Codeへの転送は完全自動
- 完了報告も自動投稿

### 2. 要約禁止・省略禁止
- Claude Codeが画面に表示したすべてのテキストを転送
- 「修正完了」だけでなく「修正内容」「期待動作」も含める
- ユーザーが全体像を把握できるよう詳細情報を提供

### 3. 重複防止
- スクリーンショット: 60秒冷却期間
- コメント: last_comment_id追跡
- タイトル: last_title_content追跡

### 4. エラーハンドリング
- API接続エラー: リトライ機能
- Unicode文字エラー: cp932コーデック対策
- 長時間実行: 10時間自動停止

---

## 🔄 自動再起動システム（Watchdog Monitor）

### 概要
GitHub Issue監視スクリプト（`private_issue_monitor_service.py`）が停止した際に自動的に再起動するシステムです。

### 🎯 実装方式：Windowsタスクスケジューラ + Watchdog Monitor

**特徴**:
- 外部から定期的にプロセスチェック（5分間隔）
- Windowsタスクスケジューラで自動実行
- 軽量・シンプル（CPU使用率: 0.1%未満）
- 複数の監視スクリプトを同時管理可能

**負荷分析**:
- **CPU使用率**: 0.1%未満（1秒未満の実行）
- **メモリ使用量**: 数MB（プロセスチェック時のみ）
- **ディスクI/O**: 数KB/日（ログファイルのみ）
- **実行頻度**: 5分に1回 = 99.67%は完全に待機状態
- **影響度**: ほぼゼロ - バックグラウンドで完全に透過的

**比較**:
- Webブラウザ: 常時100-500MB、CPU 1-5%
- Windowsアップデート: 常時50-100MB
- **このWatchdog**: 5分に1秒だけ数MB、CPU 0.1%未満

**結論**: PCへの負荷はほぼゼロです。システムリソースへの影響は無視できるレベルです。

### 📁 関連ファイル

**監視スクリプト**: `watchdog_monitor_service.py`

```python
# 監視対象スクリプト設定
MONITOR_SCRIPTS = [
    {
        "name": "Private Issue Monitor",
        "script": "private_issue_monitor_service.py",
        "enabled": True
    }
]
```

**タスクスケジューラ登録スクリプト**: `setup_watchdog_task.ps1`

**ドキュメント**: `WATCHDOG_README.md`

**ログファイル**: `watchdog_monitor.log`

### 🚀 セットアップ手順

**1. PowerShellスクリプトでタスク登録（自動）**:
```powershell
cd "C:\Users\Tenormusica\Documents\github-remote-desktop"
powershell -ExecutionPolicy Bypass -File setup_watchdog_task.ps1
```

**登録内容**:
- タスク名: `GitHubIssueWatchdog`
- 実行スクリプト: `watchdog_monitor_service.py`
- 実行間隔: 5分ごと
- 実行アカウント: 現在のユーザー

**2. 手動でタスク登録（代替方法）**:
```shell
schtasks /create /tn "GitHubIssueWatchdog" /tr "python C:\Users\Tenormusica\Documents\github-remote-desktop\watchdog_monitor_service.py" /sc minute /mo 5 /ru %USERNAME%
```

**3. タスク確認**:
```shell
# コマンドラインで確認
schtasks /query /tn "GitHubIssueWatchdog"

# GUIで確認
taskschd.msc

# PowerShellで確認
Get-ScheduledTask -TaskName "GitHubIssueWatchdog"
```

**4. 手動実行テスト**:
```shell
# コマンドラインで実行
Start-ScheduledTask -TaskName "GitHubIssueWatchdog"

# 直接実行テスト
python watchdog_monitor_service.py
```

### 🔍 動作確認

**ログファイル確認**:
```shell
type watchdog_monitor.log
```

**ログ出力例**:
```
2025-09-30 16:05:58,298 - INFO - ============================================================
2025-09-30 16:05:58,298 - INFO - Watchdog Monitor Service - 定期チェック開始
2025-09-30 16:05:58,298 - INFO - チェック時刻: 2025-09-30 16:05:58
2025-09-30 16:05:58,298 - INFO - ============================================================
2025-09-30 16:05:58,298 - INFO - 確認中: Private Issue Monitor (private_issue_monitor_service.py)
2025-09-30 16:05:58,302 - INFO - ✅ Private Issue Monitor is running (PID: 12345)
```

### 🛠 トラブルシューティング

**問題: タスクが実行されない**

原因:
- Pythonパスが正しくない
- 実行権限が不足
- タスクが無効化されている

対処:
1. Pythonパス確認: `where python`
2. タスク状態確認: `Get-ScheduledTask -TaskName "GitHubIssueWatchdog" | Format-List State`
3. タスク有効化: `Enable-ScheduledTask -TaskName "GitHubIssueWatchdog"`

**問題: 再起動が実行されない**

原因:
- スクリプトパスが間違っている
- プロセス名が一致しない
- `enabled: False` になっている

対処:
1. `watchdog_monitor_service.py` の `MONITOR_SCRIPTS` 設定確認
2. `enabled: True` に変更
3. スクリプトパスを確認

### 📊 システム連携

**自動再起動フロー**:
```
1. Windowsタスクスケジューラが5分ごとに起動
   ↓
2. watchdog_monitor_service.pyが実行
   ↓
3. 監視対象スクリプトのプロセス確認
   ↓
4a. 実行中 → ログ出力のみ
4b. 停止中 → 自動再起動実行
```

**既存システムとの関係**:
- `private_issue_monitor_service.py`: GitHub Issue → Claude Code転送（常駐）
- `watchdog_monitor_service.py`: 上記スクリプトの監視・自動再起動（5分間隔）
- `task_complete_private.py`: Claude Code → GitHub Issue報告（都度実行）
- `remote-monitor_private.py`: スクリーンショット撮影（常駐）

### 🎯 推奨設定

**初心者向け（シンプル）**:
- Watchdog Monitorのみ使用
- Windowsタスクスケジューラで5分間隔実行
- 設定変更不要

**上級者向け（最大限の安定性）**:
- Watchdog Monitor（外部監視）
- Self-Healing Monitor（内部監視、別途実装可能）
- 両方を併用して2重の自動復旧

---

## 🎯 今後の改善予定

### Phase 1: 機能拡張
- [ ] マルチペイン対応（3ペイン以上）
- [ ] コマンドプレフィックスのカスタマイズ
- [ ] スクリーンショット品質設定
- [ ] 動画撮影機能

### Phase 2: UI改善
- [ ] Web UIでの管理画面
- [ ] リアルタイムログ表示
- [ ] コマンド履歴表示
- [ ] 統計情報ダッシュボード

### Phase 3: セキュリティ強化
- [ ] GitHub Token暗号化
- [ ] アクセス制限機能
- [ ] 監査ログ
- [ ] 二要素認証対応

---

## 📚 関連ドキュメント

- GitHub Repository: `Tenormusica2024/Private`
- Issue トラッカー: `#1`
- 設定ファイル場所: `C:\Users\Tenormusica\Documents\github-remote-desktop\`
- ログファイル: `private_issue_monitor.log`, `monitor_private.log`

---

**最終更新**: 2025-10-14  
**バージョン**: v2.1.0  
**作成者**: Claude Code  
**ライセンス**: Private Use Only
