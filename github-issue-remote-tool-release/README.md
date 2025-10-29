# GitHub Issue ⇔ Claude Code 遠隔操作ツール

## 🎯 これは何？

GitHub Issueにコメントするだけで、あなたのPCで動作中のClaude Codeに自動で指示を送れるツールです。

## ✨ できること

✅ 外出先からスマホでGitHub Issueにコメント → 自宅PCのClaude Codeが自動実行  
✅ Claude Codeの作業完了報告を自動でGitHub Issueに投稿  
✅ スマホから「ss」とコメントするだけでPC画面のスクリーンショットを自動取得  
✅ 複数のプロジェクト・Issueを同時管理可能

## 🔧 必要なもの

- **Windows PC**（常時起動推奨）
- **GitHubアカウント**
- **Claude Code**（インストール済み）
- **Python 3.8以上**

## 📦 インストール方法

### ステップ1: ダウンロード

このフォルダ全体をダウンロードして、任意の場所に配置します。

### ステップ2: 依存パッケージのインストール

```cmd
pip install -r requirements.txt
```

### ステップ3: セットアップウィザード実行

```cmd
python setup_wizard.py
```

画面の指示に従って5分で完了します。以下の情報を準備してください：

1. **GitHub Personal Access Token**
   - トークン作成: https://github.com/settings/tokens
   - 必要なスコープ: `repo`（プライベートリポジトリ）または `public_repo`（パブリックのみ）

2. **監視するGitHub Issue**
   - リポジトリ名（例: `username/repository`）
   - Issue番号（例: `1`）

3. **Claude Codeの起動**
   - セットアップ中にClaude Codeを起動しておいてください
   - 座標自動検出を行います

### ステップ4: 監視サービス起動

```cmd
python monitor_service.py
```

このコマンドでClaude Codeの監視を開始します。**PCをスリープさせずに起動したままにしてください。**

## 📱 使い方

### 基本的な使用方法

1. **GitHub Issueにコメントを書く**
   - `upper: このファイルのバグを修正して` → Claude Code上部ペインに送信
   - `lower: プロジェクトの進捗を教えて` → Claude Code下部ペインに送信
   - `ss` → 自宅PCのスクリーンショットを自動撮影・投稿

2. **自宅PCのClaude Codeが自動で指示を受け取り実行**

3. **完了したら自動でGitHub Issueに報告**
   - Claude Codeが自動で `task_complete.py` を実行

### スマホから使う

1. **GitHubアプリで自分のIssueを開く**
2. **コメント欄に指示を入力**
   - `upper: 〇〇を実行して` または `lower: △△を確認して`
3. **自宅PCが自動実行 → 結果通知**

### コマンド一覧

| コマンド | 説明 | 例 |
|---------|------|-----|
| `upper: [指示]` | Claude Code上部ペインに送信 | `upper: app.pyのバグを修正して` |
| `lower: [指示]` | Claude Code下部ペインに送信 | `lower: ログを確認して` |
| `ss` | スクリーンショット撮影 | `ss` |

## 🔄 複数プロジェクトでの使用

プロジェクトごとに異なるフォルダを作成し、それぞれで `setup_wizard.py` を実行してください。

```
project-a/
  ├── monitor_service.py
  ├── task_complete.py
  ├── config.json  ← プロジェクトA用の設定
  └── ...

project-b/
  ├── monitor_service.py
  ├── task_complete.py
  ├── config.json  ← プロジェクトB用の設定
  └── ...
```

各フォルダで `monitor_service.py` を起動すれば、複数のIssueを同時監視できます。

## ⚠️ よくある質問

### Q: セットアップで座標検出に失敗します

**A:** 以下を確認してください：
- Claude Codeが起動していますか？
- Claude Codeウィンドウがアクティブ（前面）になっていますか？
- ウィンドウタイトルに「Claude」が含まれていますか？

手動調整も可能です。セットアップウィザードで「座標を手動調整しますか？」と聞かれたら `y` と入力してください。

### Q: 複数のプロジェクトで使えますか？

**A:** はい。プロジェクトごとにフォルダを分けて、それぞれで `setup_wizard.py` を実行してください。

### Q: PCをスリープさせても動きますか？

**A:** いいえ。監視サービスを動作させるにはPCを起動状態に保つ必要があります。

### Q: Claude Codeが応答しない場合は？

**A:** 以下を確認してください：
1. `monitor_service.py` が起動していますか？
2. `monitor_service.log` ファイルにエラーが記録されていませんか？
3. Claude Codeウィンドウの座標が正しいですか？（`config.json` を確認）

### Q: GitHub Issueへの投稿が失敗します

**A:** 以下を確認してください：
1. GitHub Personal Access Tokenが有効ですか？
2. トークンに `repo` または `public_repo` スコープがありますか？
3. リポジトリ名とIssue番号が正しいですか？

### Q: スクリーンショットがアップロードされません

**A:** 以下を確認してください：
1. GitHub Personal Access Tokenに `repo` スコープがありますか？
2. リポジトリに書き込み権限がありますか？
3. インターネット接続は正常ですか？

## 📝 設定ファイル（config.json）

セットアップウィザードで自動生成される設定ファイルの構造：

```json
{
  "github_token": "github_pat_...",
  "github_repo": "username/repository",
  "issue_number": "1",
  "poll_interval": 5,
  "claude_code_coords": {
    "upper": [1357, 539],
    "lower": [1357, 1056]
  }
}
```

- `github_token`: GitHub Personal Access Token
- `github_repo`: 監視するリポジトリ（`owner/repo`形式）
- `issue_number`: 監視するIssue番号
- `poll_interval`: 監視間隔（秒）
- `claude_code_coords`: Claude Code入力欄の座標
  - `upper`: 上部ペイン座標 [x, y]
  - `lower`: 下部ペイン座標 [x, y]

## 🛠 トラブルシューティング

### 監視サービスが起動しない

```
❌ 初期化エラー: config.jsonが見つかりません
```

**解決方法**: `setup_wizard.py` を実行して設定ファイルを生成してください。

### コメントが転送されない

```
[ERROR] GitHub API接続エラー
```

**解決方法**:
1. インターネット接続を確認
2. GitHub Personal Access Tokenの有効性を確認
3. `config.json` の設定を確認

### Claude Codeに貼り付けられない

```
[ERROR] Claude Code貼り付けエラー
```

**解決方法**:
1. Claude Codeが起動しているか確認
2. `config.json` の座標設定を確認
3. 座標を再設定: `python setup_wizard.py` を再実行

## 📞 サポート

問題が解決しない場合は、以下の情報を添えてサポートにお問い合わせください：

1. `monitor_service.log` ファイルの内容
2. エラーメッセージのスクリーンショット
3. 使用しているPython のバージョン（`python --version`）
4. OSのバージョン

## 🔐 セキュリティ

- **GitHub Personal Access Tokenは絶対に公開しないでください**
- `config.json` ファイルは `.gitignore` に追加してGitにコミットしないでください
- トークンは定期的に再生成することを推奨します

## 📜 ライセンス

このツールは買い切り有料ソフトウェアです。  
再配布・改変・商用利用は購入者のみ許可されます。

## 🔄 アップデート

新しいバージョンがリリースされた場合は、購入時のメールに通知が届きます。  
最新版のダウンロードリンクから更新してください。

---

**バージョン**: 1.0.0  
**最終更新**: 2025-01-19  
**製作者**: GitHub Issue Remote Tool Development Team