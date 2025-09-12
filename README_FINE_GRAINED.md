# GitHub Remote Desktop - Fine-grained Token Setup Guide

## Fine-grained Personal Access Token とは

Fine-grained Personal Access Tokenは、GitHub の新しいトークン形式で、以下の特徴があります：

- **リポジトリ単位でのアクセス制御**: 特定のリポジトリのみにアクセス権限を限定
- **詳細な権限設定**: 必要最小限の権限のみを付与
- **より安全**: 従来のClassic tokenより細かい制御が可能

## 🚀 Fine-grained Token セットアップ手順

### 1. Fine-grained Token の作成

1. **GitHub にログイン** → **Settings** → **Developer settings** → **Personal access tokens** → **Fine-grained tokens**

2. **Generate new token** をクリック

3. **Token name**: `web-remote-desktop-token` (任意の名前)

4. **Expiration**: お好みの期間（最大1年）

5. **Repository access**: 
   - **Selected repositories** を選択
   - `Tenormusica2024/web-remote-desktop` を選択

6. **Repository permissions** で以下を設定:
   ```
   Contents: Read and Write    (スクリーンショットファイルアップロード用)
   Issues: Read and Write      (Issue監視・コメント投稿用)
   Metadata: Read             (リポジトリ情報取得用)
   ```

7. **Generate token** をクリックしてトークンをコピー

### 2. トークンの設定

専用の設定スクリプトを実行：

```bash
python setup_fine_grained_token.py
```

トークンの入力を求められたら、コピーしたFine-grained tokenを貼り付けてください。

### 3. 権限テスト

Fine-grained tokenの権限が正しく設定されているかテスト：

```bash
python test_fine_grained_access.py
```

全てのテストが通れば設定完了です。

### 4. システム動作テスト

```bash
# テスト実行
python remote-monitor.py --test

# 監視開始
python remote-monitor.py
```

## 🔧 トラブルシューティング

### Token形式エラー

```
[ERROR] Token doesn't appear to be a Fine-grained token
```

**解決**: Fine-grained tokenは `gho_`, `ghu_`, `ghs_` で始まります。Classic token (`ghp_`) ではありません。

### 権限エラー

```
[ERROR] Issues write failed: 403
```

**解決**: Fine-grained tokenの権限設定を確認：
1. GitHub Settings → Personal access tokens → Fine-grained tokens
2. 該当トークンの **Repository permissions** を確認
3. `Issues: Read and Write` が設定されているか確認

### リポジトリアクセスエラー

```
[ERROR] Repository access failed: 404
```

**解決**: 
1. Fine-grained tokenの **Repository access** 設定を確認
2. `Tenormusica2024/web-remote-desktop` が選択されているか確認
3. リポジトリが存在することを確認

## 📋 必要な権限一覧

| 権限 | レベル | 用途 |
|------|--------|------|
| **Contents** | Read and Write | スクリーンショットファイルのGitHubへのアップロード |
| **Issues** | Read and Write | Issue監視、コメントの読み取り・投稿 |
| **Metadata** | Read | リポジトリの基本情報取得 |

## 🔄 Classic Token からの移行

既存のClassic token (`ghp_`) を使用している場合：

1. Fine-grained tokenを新規作成
2. `python setup_fine_grained_token.py` で新しいトークンを設定
3. `python test_fine_grained_access.py` で動作確認

## 💡 利点

Fine-grained tokenを使用することで：

- **セキュリティ向上**: 必要最小限の権限のみ付与
- **アクセス制限**: 特定のリポジトリのみにアクセス
- **監査可能**: より詳細なアクセスログ

---

**Note**: Fine-grained tokenは比較的新しい機能です。問題が発生した場合は Classic token も使用可能ですが、セキュリティの観点から Fine-grained token の使用を推奨します。