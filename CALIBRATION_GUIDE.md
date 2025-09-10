# キャリブレーションガイド

## 現在の状況
✅ **システム実装完了**  
✅ **GitHub Issue #3作成完了**  
✅ **テストコメント投稿完了** (ID: 3233831909)  
✅ **全テスト通過**

## キャリブレーション手順

### 1. Claude Codeを開く
Claude Codeアプリケーションを開いて、以下の状態にしてください：
- 右上と右下の入力欄が見える状態
- ウィンドウサイズと位置を固定

### 2. キャリブレーション実行
```bash
cd C:\Users\Tenormusica\cc-snap-to-github
python gh_issue_to_claude_paste.py --calibrate
```

### 3. 座標登録
スクリプトの指示に従って：
1. **右上入力欄**にマウスカーソルを置いて Enter
2. **右下入力欄**にマウスカーソルを置いて Enter

### 4. システム開始
```bash
python gh_issue_to_claude_paste.py
```

### 5. テスト確認
以下のメッセージがClaude Codeの下部ペインに表示されるはずです：

```
システムテストです

これはGitHub Issue to Claude Codeシステムのテストコメントです。
このメッセージが下部ペインに表示されれば成功です。

テスト時刻: $(date)
```

## 追加テスト

システムが動作したら、GitHub Issue #3に以下のテストコメントを投稿してみてください：

### 右上ペインテスト
```
upper: 右上ペインのテストメッセージです
```

### 右下ペインテスト  
```
lower: 右下ペインのテストメッセージです
```

### デフォルトペインテスト
```
プレフィックスなしのテストメッセージです
```

## トラブルシューティング

### 座標がずれる場合
```bash
python gh_issue_to_claude_paste.py --calibrate
```
を再実行して座標を再設定

### システムが反応しない場合
1. 環境変数の確認
2. GitHubトークンの権限確認
3. プロセスが動作しているか確認

### コメントが表示されない場合
1. ONLY_AUTHOR設定の確認（Tenormusica2024のみ処理）
2. コメントの書式確認（upper:/lower:）
3. ネットワーク接続確認

## 成功確認

以下が確認できればシステム完成です：
- ✅ Issue #3のコメントがClaude Codeに自動送信される
- ✅ upper:/lower:の書式で送信先を制御できる
- ✅ 日本語と英語の混在テキストが正常に処理される

## Issue URLs
- **スクリーンショット用**: https://github.com/Tenormusica2024/web-remote-desktop/issues/1
- **リモート制御用**: https://github.com/Tenormusica2024/web-remote-desktop/issues/3