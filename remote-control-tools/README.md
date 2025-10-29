# GitHub Issue ⇔ Claude Code 連携システム - Remote Control Tools

**Private Repository対応版 - GitHub Issue経由でClaudeCodeを完全遠隔操作**

## 🎯 システム概要

3つの主要ツールで構成される双方向連携システム:

### 1. private_issue_monitor_service.py（GitHub → Claude Code転送）
- **GitHub Issue #1のコメントを自動監視し、Claude Codeに転送**
- `upper:` コマンド → Claude Code上部ペインに入力
- `lower:` コマンド → Claude Code下部ペインに入力
- `ss` コマンド → スクリーンショット自動撮影・アップロード
- **5秒間隔の高速ポーリング監視**
- **GitHub API全ページ取得対応（100件超のコメント対応）**
- **重複処理防止・キャッシュ回避機能**

### 2. task_complete_private.py（Claude Code → GitHub転送）
- **Claude Codeの作業完了報告をGitHub Issue #1に自動投稿**
- タスク完了時の詳細情報を完全転送（要約禁止）
- 修正内容・改善内容・期待動作などの詳細情報を含む
- GitHub Markdown形式の改行対応（スラッシュ区切り対応）
- Private repository完全対応

### 3. remote-monitor_private.py（スクリーンショット自動化）
- **GitHub Issue #1の「ss」コメントを検知して自動スクリーンショット撮影**
- 撮影した画像をGitHubリポジトリにアップロード
- 結果をIssueコメントで報告（画像プレビュー付き）
- **10時間自動停止機能**（長時間実行制限）
- タイトルベースのコマンド対応
- 重複実行防止（冷却期間60秒）

## 📁 ファイル構成

```
github-remote-desktop/
├── private_issue_monitor_service.py    # メイン監視サービス（GitHub → Claude Code）
├── task_complete_private.py            # 完了報告ツール（Claude Code → GitHub）
├── remote-monitor_private.py           # スクリーンショット自動化
├── .env_private                        # Private repository設定ファイル
├── .gh_issue_to_claude_state_private_service.json  # 状態管理（last_comment_id）
├── .gh_issue_to_claude_coords_private_new.json     # Claude Code座標設定
├── last_comment_id_private.txt         # スクリーンショットシステム状態
├── last_title_content_private.txt      # タイトルコマンド重複防止
└── logs/
    ├── private_issue_monitor.log       # 監視サービスログ
    └── monitor_private.log             # スクリーンショットシステムログ
```

## ⚙️ セットアップ

### 1. 依存関係インストール
```bash
pip install requests pyautogui pyperclip python-dotenv
```

### 2. GitHub Private Repository設定

`.env_private`ファイルを作成:
```env
GH_REPO=Tenormusica2024/Private
GH_ISSUE=1
GH_TOKEN=github_pat_your_personal_access_token
POLL_SEC=5

# task_complete_private.py用
GITHUB_TOKEN=github_pat_your_personal_access_token
GITHUB_REPO=Tenormusica2024/Private
MONITOR_ISSUE_NUMBER=1

# remote-monitor_private.py用
GITHUB_BRANCH=master
POLL_INTERVAL=30
```

### 3. Claude Code座標設定

`.gh_issue_to_claude_coords_private_new.json`を作成:
```json
{
  "upper": [1357, 539],
  "lower": [1357, 1056]
}
```

**座標の設定方法:**
- Claude Codeを開いた状態でマウス座標を確認
- 上部ペイン（プロンプト入力欄）のクリック位置
- 下部ペイン（コマンドライン入力欄）のクリック位置

### 4. システム起動

```bash
# メイン監視サービス起動（バックグラウンド実行推奨）
cd "C:\Users\Tenormusica\Documents\github-remote-desktop"
python private_issue_monitor_service.py

# スクリーンショット監視サービス起動（別ウィンドウ）
python remote-monitor_private.py
```

## 🚀 使用方法

### GitHub Issue #1での操作コマンド

#### 1. 上部ペインへの入力
```
upper: README.mdを更新してください
```
→ Claude Code上部ペイン（通常のプロンプト入力欄）に転送

#### 2. 下部ペインへの入力
```
lower: git status
```
→ Claude Code下部ペイン（Bashコマンド入力欄）に転送

#### 3. スクリーンショット撮影
```
ss
```
→ 即座にスクリーンショット撮影・アップロード・Issue投稿

### Claude Code側での完了報告

作業完了時に以下のコマンドを実行:
```bash
cd "C:\Users\Tenormusica\Documents\github-remote-desktop" && python task_complete_private.py "作業完了の詳細内容"
```

**重要な設計思想:**
- **要約・省略・短縮は一切禁止**
- 画面に表示されている完了報告の全テキストをそのまま記載
- 修正内容・変更点・期待される動作などの詳細情報を全て含める

## 🔧 技術詳細

### private_issue_monitor_service.py の主要機能

1. **GitHub API全ページ取得**
   - `per_page=100` + ページネーション対応
   - キャッシュ回避パラメータ（`_t=timestamp`）
   - ETAGヘッダー対応

2. **コマンド処理**
   - `upper:` → 上部ペイン転送 + 完了報告指示追加
   - `lower:` → 下部ペイン転送 + 完了報告指示追加
   - `ss` → スクリーンショット撮影（完全一致のみ）

3. **重複防止機構**
   - `last_comment_id` による状態管理
   - 処理済みコメントID記録（`processed_screenshot_comments`）
   - スクリーンショット冷却期間（60秒）

4. **自動復旧機能**
   - 連続エラー10回まで許容
   - エラー時の待機時間自動延長
   - 予期しないエラーでも30秒後に再起動

### task_complete_private.py の主要機能

1. **GitHub Markdown改行対応**
   - スラッシュ区切り（` / `, `/`）を `\n\n` に変換
   - 段落間の適切なスペーシング

2. **完全転送の保証**
   - コマンドライン引数で詳細メッセージを受け取る
   - 要約処理を一切実施しない
   - タイムスタンプと実行者情報を自動付与

3. **Private Repository対応**
   - Bearer認証ヘッダー使用
   - `.env_private` 優先読み込み

### remote-monitor_private.py の主要機能

1. **コメント監視**
   - 「ss」コメント検知（完全一致）
   - システムコメント除外（自己投稿防止）
   - 重複コメント処理防止

2. **タイトル監視**
   - Issue #1のタイトルで「ss」を検知
   - タイトル内容でハッシュ管理（重複防止）

3. **スクリーンショット処理**
   - PyAutoGUIで全画面撮影
   - GitHub APIでリポジトリにアップロード
   - 結果をIssueコメントで報告（画像プレビュー付き）

4. **10時間自動停止**
   - 起動から36000秒（10時間）で自動停止
   - 1時間ごとに残り時間をログ出力

## 📊 システムフロー

### GitHub → Claude Code転送フロー
```
GitHub Issue #1コメント投稿
  ↓
private_issue_monitor_service.py が検知（5秒ポーリング）
  ↓
コマンド判定（upper: / lower: / ss）
  ↓
該当ペインにクリップボード経由で貼り付け
  ↓
完了報告指示を自動追加（upper/lower のみ）
```

### Claude Code → GitHub転送フロー
```
Claude Code作業完了
  ↓
task_complete_private.py 実行
  ↓
完了報告内容をGitHub API経由で投稿
  ↓
Issue #1にコメント追加（タイムスタンプ付き）
```

### スクリーンショット自動化フロー
```
「ss」コメント投稿 or タイトル変更
  ↓
remote-monitor_private.py が検知（30秒ポーリング）
  ↓
PyAutoGUIで全画面撮影
  ↓
GitHub APIでアップロード（screenshots/YYYY/MM/ファイル名.png）
  ↓
結果をIssueコメントで報告（画像プレビュー付き）
```

## 🛡️ セキュリティ

- **Bearer認証**: GitHub Personal Access Token使用
- **環境変数管理**: `.env_private` でトークン保護
- **Private Repository対応**: 社内限定アクセス
- **ログファイル**: 機密情報フィルタリング（ASCII変換）
- **最小権限原則**: Issues, Contents権限のみ

## 📝 ログとモニタリング

### ログファイル
- `private_issue_monitor.log` - メイン監視サービス
- `monitor_private.log` - スクリーンショットシステム

### 状態管理ファイル
- `.gh_issue_to_claude_state_private_service.json` - 最終処理コメントID
- `last_comment_id_private.txt` - スクリーンショット最終処理ID
- `last_title_content_private.txt` - タイトルコマンド重複防止

### デバッグレベルログ
- 全コメント取得状況
- コマンド判定プロセス
- 座標・貼り付け動作
- GitHub APIレスポンス

## 🔄 トラブルシューティング

### 問題1: コマンドが転送されない
**原因**: 座標設定が不正確、またはClaude Codeウィンドウが非表示
**解決策**:
1. Claude Codeを前面に表示
2. `.gh_issue_to_claude_coords_private_new.json` の座標を再設定
3. `private_issue_monitor.log` でエラー確認

### 問題2: 完了報告が投稿されない
**原因**: GitHub Token権限不足、またはコマンド実行漏れ
**解決策**:
1. `.env_private` のトークン確認
2. `task_complete_private.py` 実行確認
3. Claude Codeの指示文で実行を明示

### 問題3: スクリーンショットが重複投稿
**原因**: 冷却期間中の連続実行
**解決策**:
1. 60秒間の冷却期間を待つ
2. `last_title_content_private.txt` と `last_comment_id_private.txt` を削除して状態リセット

### 問題4: GitHub API Rate Limit
**原因**: 短時間に大量のAPI呼び出し
**解決策**:
1. `POLL_SEC` と `POLL_INTERVAL` を増やす（10秒以上推奨）
2. GitHub APIレート制限を確認（5000 requests/hour）

## 🚀 今後の改善予定

### フェーズ1: 安定性向上
- [ ] WebSocket対応（リアルタイム通知）
- [ ] エラーリトライ機構の強化
- [ ] ヘルスチェック機能

### フェーズ2: 機能拡張
- [ ] マルチペイン対応（3ペイン以上）
- [ ] ファイルアップロード機能
- [ ] コマンド履歴管理UI

### フェーズ3: 運用最適化
- [ ] Dockerコンテナ化
- [ ] Systemdサービス化（Linux）
- [ ] Windows Serviceインストーラー

## 📚 関連ドキュメント

- **Notion完全ドキュメント**: [GitHub Issue ⇔ Claude Code 連携システム完全ドキュメント](https://www.notion.so/27ec949421c4812eba59dd0c5153c058)
- **GitHub Repository**: [Tenormusica2024/Private](https://github.com/Tenormusica2024/Private)
- **監視対象Issue**: [Private Repository Issue #1](https://github.com/Tenormusica2024/Private/issues/1)

## 🔄 アップデート履歴

### v2.0 (2025-09-30) - Private Repository完全対応版
- **3ツール統合構成**: private_issue_monitor_service.py, task_complete_private.py, remote-monitor_private.py
- **双方向連携**: GitHub ⇔ Claude Code完全自動化
- **完全転送設計**: 要約禁止・詳細情報の完全記録
- **重複防止強化**: 状態管理ファイル + 冷却期間
- **Notion完全ドキュメント**: 全ツール詳細情報記載

### v1.1 (2025-09-12)
- **セキュリティ強化**: 環境変数GITHUB_TOKEN対応
- **Push Protection対応**: ハードコードトークン除去

### v1.0 (Initial Release)
- GitHub Issue #1完全対応
- SSスクリーンショット + Claude Code制御統合
- 111+コメント対応（GitHub API pagination）

---

**GitHub Issue ⇔ Claude Code連携システム - Private Repository完全対応版**  
*完全自動化・双方向連携・詳細情報記録による最適なリモート開発環境*