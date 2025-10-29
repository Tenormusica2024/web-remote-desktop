# GitHub Issue ⇔ Claude Code 遠隔操作ツール (v2)

## 🎯 これは何？

GitHub Issueにコメントするだけで、あなたのPCで動作中のClaude Codeに自動で指示を送れるツールです。

**v2の新機能:**
- ✅ **ウィンドウ直接操作**: 座標設定不要、Claude Codeを自動検出
- ✅ **複数Issue同時監視**: 複数のGitHub Issueを同時監視可能
- ✅ **複数ウィンドウ対応**: 別窓で開いた複数のClaude Codeを個別指定可能
- ✅ **マルチモニター対応**: サブモニターやウィンドウ位置に依存しない
- ✅ **簡単セットアップ**: 座標調整の手間を完全排除
- ✅ **柔軟なURL形式**: 標準URL・省略形式・スペース区切りに対応

## ✨ できること

✅ 外出先からスマホでGitHub Issueにコメント → 自宅PCのClaude Codeが自動実行  
✅ Claude Codeの作業完了報告を自動でGitHub Issueに投稿  
✅ スマホから「ss」とコメントするだけでPC画面のスクリーンショットを自動取得  
✅ 複数のClaude Codeウィンドウを個別指定して操作可能

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

2. **監視するGitHub Issue URL**
   - 形式: `https://github.com/owner/repository/issues/番号`
   - 省略形式も可: `ttps://github.com/owner/repository/issues/番号`（hなし）
   - スペース区切りも可: `https: //github.com /owner/ repository/ issues/ 番号`
   - 例: `https://github.com/octocat/Hello-World/issues/1`
   - **複数のIssueを登録可能**（1つずつ追加）

3. **Claude Codeの起動**
   - セットアップ中にClaude Codeを起動しておくと自動検出されます
   - 起動していなくても設定可能（監視サービス実行時に自動検出）

### ステップ4: 監視サービス起動

**単一Issue監視（標準版）:**
```cmd
python monitor_service.py
```

**複数Issue同時監視（マルチ版）:**
```cmd
python monitor_service_multi.py
```

このコマンドでClaude Codeの監視を開始します。**PCをスリープさせずに起動したままにしてください。**

**💡 どちらを使うべき？**
- **monitor_service.py**: 1つのIssueのみ監視（シンプル・軽量）
- **monitor_service_multi.py**: 複数Issue同時監視（setup_wizard.pyで複数登録した場合）

## 📱 使い方

### 基本的な使用方法

1. **GitHub Issueにコメントを書く**
   - `#1: このファイルのバグを修正して` → 1番目のClaude Codeに送信
   - `#2: プロジェクトの進捗を教えて` → 2番目のClaude Codeに送信
   - `ss` → 自宅PCのスクリーンショットを自動撮影・投稿
   - コマンドなし → デフォルトで1番目のClaude Codeに送信

2. **自宅PCのClaude Codeが自動で指示を受け取り実行**

3. **完了したら自動でGitHub Issueに報告**
   - Claude Codeが自動で `task_complete.py` を実行

### スマホから使う

1. **GitHubアプリで自分のIssueを開く**
2. **コメント欄に指示を入力**
   - `#1: 〇〇を実行して` または `#2: △△を確認して`
3. **自宅PCが自動実行 → 結果通知**

### コマンド一覧

| コマンド | 説明 | 例 |
|---------|------|-----|
| `#1: [指示]` | 1番目のClaude Codeに送信 | `#1: app.pyのバグを修正して` |
| `#2: [指示]` | 2番目のClaude Codeに送信 | `#2: ログを確認して` |
| `#3: [指示]` | 3番目のClaude Codeに送信 | `#3: テストを実行して` |
| コマンドなし | デフォルト（1番目）に送信 | `このファイルを整理して` |
| `ss` | スクリーンショット撮影 | `ss` |

## 🔄 複数Issueの監視方法

### 方法1: 同一フォルダで複数Issue監視（推奨）

セットアップウィザードで複数のIssue URLを登録し、`monitor_service_multi.py` を実行：

```cmd
python setup_wizard.py  # 複数のIssue URLを1つずつ追加
python monitor_service_multi.py  # すべて同時監視
```

**メリット:**
- 1つの監視プロセスで複数Issueを処理
- 設定ファイル1つで管理
- リソース効率が良い

### 方法2: プロジェクトごとに別フォルダ

プロジェクトごとに異なるフォルダを作成し、それぞれで `setup_wizard.py` を実行：

```
project-a/
  ├── monitor_service.py
  ├── task_complete.py
  ├── config.json  ← プロジェクトA用の設定（Issue 1つ）
  └── ...

project-b/
  ├── monitor_service.py
  ├── task_complete.py
  ├── config.json  ← プロジェクトB用の設定（Issue 1つ）
  └── ...
```

各フォルダで `monitor_service.py` を起動すれば、複数のIssueを同時監視できます。

**メリット:**
- プロジェクトごとに完全独立
- 個別に起動・停止可能
- 設定の分離が明確

## 🪟 複数ウィンドウの使い方

### Claude Codeを複数起動する方法

1. **新しいウィンドウで開く**
   - Claude Codeで「ファイル」→「新しいウィンドウ」
   - または `claude` コマンドを複数回実行

2. **ウィンドウ番号の確認**
   - セットアップウィザード実行時に自動検出された順序が番号になります
   - 監視サービス起動時のログでも確認可能

3. **コマンドで指定**
   - `#1: 指示` → 1番目のウィンドウ
   - `#2: 指示` → 2番目のウィンドウ
   - 番号指定なし → 自動的に1番目に送信

### ウィンドウ番号の割り当て

- 検出された順番に自動で番号が割り当てられます
- ウィンドウタイトルに「claude」を含むものが対象
- 非表示ウィンドウは無視されます

## ⚠️ よくある質問

### Q: セットアップ時にClaude Codeが検出されません

**A:** 以下を確認してください：
- Claude Codeが起動していますか？
- ウィンドウタイトルに「Claude」が含まれていますか？
- ウィンドウが最小化されていませんか？

セットアップ時に検出されなくても問題ありません。監視サービス実行時に自動検出されます。

### Q: 複数のIssueを同時監視できますか？

**A:** はい。2つの方法があります：

**方法1（推奨）:** セットアップウィザードで複数Issue URLを登録し、`monitor_service_multi.py` を実行
```cmd
python setup_wizard.py  # Issue URLを複数登録
python monitor_service_multi.py  # 同時監視開始
```

**方法2:** プロジェクトごとにフォルダを分けて、それぞれで `monitor_service.py` を実行

### Q: PCをスリープさせても動きますか？

**A:** いいえ。監視サービスを動作させるにはPCを起動状態に保つ必要があります。

### Q: Claude Codeが応答しない場合は？

**A:** 以下を確認してください：
1. `monitor_service.py` が起動していますか？
2. `monitor_service.log` ファイルにエラーが記録されていませんか？
3. Claude Codeが起動していますか？
4. Claude Codeが応答可能な状態ですか？（フリーズしていないか）

### Q: ウィンドウ番号を変更できますか？

**A:** ウィンドウ番号は検出順に自動割り当てされます。順序を変更したい場合は：
1. 監視サービスを停止
2. Claude Codeのウィンドウを閉じる
3. 希望する順序でClaude Codeを起動
4. 監視サービスを再起動

### Q: マルチモニター環境でも動作しますか？

**A:** はい。v2ではウィンドウを直接操作するため、モニター配置やウィンドウ位置に依存しません。

### Q: 既存の座標方式（v1）から移行できますか？

**A:** はい。v2は完全な新方式のため、以下の手順で移行してください：
1. 新しいフォルダにv2をダウンロード
2. `setup_wizard.py` を実行して再設定
3. 旧バージョンの監視サービスを停止
4. v2の監視サービスを起動

## 📝 設定ファイル（config.json）

セットアップウィザードで自動生成される設定ファイルの構造：

### 単一Issue監視（monitor_service.py用）
```json
{
  "github_token": "github_pat_...",
  "github_repo": "username/repository",
  "issue_number": "1",
  "poll_interval": 5
}
```

### 複数Issue監視（monitor_service_multi.py用）
```json
{
  "github_token": "github_pat_...",
  "issues": [
    {
      "url": "https://github.com/owner/repo1/issues/1",
      "enabled": true
    },
    {
      "url": "https://github.com/owner/repo2/issues/5",
      "enabled": true
    }
  ],
  "poll_interval": 5
}
```

**パラメータ説明:**
- `github_token`: GitHub Personal Access Token
- `github_repo`: 監視するリポジトリ（単一Issue版のみ）
- `issue_number`: 監視するIssue番号（単一Issue版のみ）
- `issues`: 監視するIssue URLのリスト（複数Issue版のみ）
  - `url`: Issue URL（標準形式・省略形式・スペース区切りに対応）
  - `enabled`: 監視有効/無効（`true`で有効、`false`で無効化）
- `poll_interval`: 監視間隔（秒）

**URL形式の柔軟性:**
- 標準: `https://github.com/owner/repo/issues/1`
- 省略: `ttps://github.com/owner/repo/issues/1` (hなし)
- スペース区切り: `https: //github.com /owner/ repo/ issues/ 1`

すべて同じIssueとして認識されます。

**v1との違い:** `claude_code_coords` フィールドが削除されました（座標不要）

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

### Claude Codeウィンドウが見つかりません

```
❌ Claude Codeウィンドウが見つかりません
```

**解決方法**:
1. Claude Codeが起動しているか確認
2. ウィンドウタイトルに「Claude」が含まれているか確認
3. ウィンドウが最小化されていないか確認
4. `monitor_service.log` で詳細を確認

### テキストが送信されない

**チェックリスト**:
- [ ] Claude Codeが起動していますか？
- [ ] Claude Codeがフリーズしていませんか？
- [ ] 手動でClaude Codeにテキスト入力できますか？
- [ ] ウィンドウがアクティブになりますか？

**デバッグ手順**:
1. Claude Codeを再起動
2. `window_detector_test.py test` でテスト送信
3. `monitor_service.log` でエラー詳細を確認

## 📞 サポート

問題が解決しない場合は、以下の情報を添えてサポートにお問い合わせください：

1. `monitor_service.log` ファイルの内容
2. エラーメッセージのスクリーンショット
3. 使用しているPython のバージョン（`python --version`）
4. OSのバージョン
5. Claude Codeのバージョン

## 🔐 セキュリティ

- **GitHub Personal Access Tokenは絶対に公開しないでください**
- `config.json` ファイルは `.gitignore` に追加してGitにコミットしないでください
- トークンは定期的に再生成することを推奨します

## 📜 ライセンス

このツールは買い切り有料ソフトウェアです。  
再配布・改変・商用利用は購入者のみ許可されます。

## 🔄 アップデート

### v2の変更点

- ✅ 座標方式を廃止、ウィンドウ直接操作方式に変更
- ✅ 複数Issue同時監視機能を追加（`monitor_service_multi.py`）
- ✅ 複数ウィンドウの個別指定機能を追加（#1:, #2:, #3:）
- ✅ マルチモニター・任意配置に完全対応
- ✅ セットアップの簡素化（座標調整を完全排除）
- ✅ 3つの送信方法によるフォールバック機能
- ✅ 柔軟なURL形式サポート（標準・省略・スペース区切り）

### v1からの移行

v1（座標方式）をご使用の場合、v2（ウィンドウ直接操作方式）への移行を推奨します：

1. v2フォルダをダウンロード
2. `setup_wizard.py` を実行
3. v1の監視サービスを停止
4. v2の監視サービスを起動

---

**バージョン**: 2.1.0  
**最終更新**: 2025-01-30  
**製作者**: GitHub Issue Remote Tool Development Team

## 🆕 v2.1.0 新機能

- ✅ **複数Issue同時監視**: 1つの監視プロセスで複数のGitHub Issueを監視
- ✅ **柔軟なURL形式**: 標準URL、省略形式（ttps://）、スペース区切りに対応
- ✅ **個別状態管理**: Issue毎に独立した状態ファイルで最終コメントID管理
- ✅ **動的有効/無効切替**: config.jsonの`enabled`フラグでIssue監視を制御