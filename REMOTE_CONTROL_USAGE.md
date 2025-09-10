# Claude Code リモート制御システム使用ガイド

## システム概要

GitHub Issue #3 にコメントを投稿すると、自動的にClaude Codeの入力欄にテキストが送信されるシステムです。

## 現在のシステム状況

- ✅ **メインスクリプト**: `gh_issue_to_claude_paste.py` 作成完了
- ✅ **GitHub Issue**: Issue #3 作成完了 ([リンク](https://github.com/Tenormusica2024/web-remote-desktop/issues/3))
- ✅ **依存関係**: pyautogui, pyperclip, pillow インストール済み
- ✅ **環境変数**: 設定完了

## 次の手順

### 1. キャリブレーション（初回のみ必須）

```bash
python gh_issue_to_claude_paste.py --calibrate
```

このコマンドを実行後：
1. Claude Codeを開いて、右上の入力欄にマウスを置いてEnter
2. 右下の入力欄にマウスを置いてEnter  
3. 座標が保存されます

### 2. システム開始

```bash
python gh_issue_to_claude_paste.py
```

### 3. 使用方法

GitHub Issue #3 に以下の形式でコメント投稿：

#### 基本書式
- `upper: メッセージ` → 右上ペインに送信
- `lower: メッセージ` → 右下ペインに送信
- プレフィックスなし → 下部ペイン（デフォルト）に送信

#### 使用例

```
upper: YouTubeの文字起こし機能について教えて
```

```
lower: このコードにバグがありますか？

def hello():
    print("Hello World")
```

```
Claude Codeの使い方を教えて
```

## システム設定

- **監視対象**: Issue #3 (`Tenormusica2024/web-remote-desktop`)
- **ポーリング間隔**: 5秒
- **処理対象ユーザー**: Tenormusica2024のみ
- **デフォルトペイン**: lower（下部）
- **自動実行**: コメント投稿後、自動でEnterキー実行

## 既存システムとの連携

**スクリーンショットシステム**（Issue #1）と併用可能：
1. `ss` でスクリーンショット取得 → 現在の画面確認
2. Issue #3 でコマンド送信 → Claude Codeを操作
3. `ss` で結果確認

## トラブルシューティング

### よくある問題

1. **座標がずれる**
   - ウィンドウ配置を変えた場合は再キャリブレーション必要
   - `python gh_issue_to_claude_paste.py --calibrate`

2. **反応しない**
   - 環境変数が設定されているか確認
   - GitHubトークンの権限確認
   - プロセスが動作しているか確認

3. **文字化け**
   - 日本語はクリップボード経由で安全に処理されます

### ログ確認

システムの動作ログは以下のファイルで確認：
- `.gh_issue_to_claude_state.json` - 既読管理
- `.gh_issue_to_claude_coords.json` - 座標設定

## セキュリティ注意事項

- GitHubトークンは適切な権限（repo または public_repo）を設定
- ONLY_AUTHOR設定により、指定ユーザー以外のコメントは無視
- プライベートリポジトリの使用を推奨

---

**次のステップ**: キャリブレーション → システム開始 → Issue #3 でテスト投稿