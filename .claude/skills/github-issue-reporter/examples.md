# GitHub Issue Reporter - 使用例

## Example 1: タスク完了報告

**シナリオ**: ファイルの修正とデプロイが完了した場合

```bash
cd "C:\Users\Tenormusica\Documents\github-remote-desktop" && python task_complete_private.py "## タスク完了: UI修正

### 実施内容
- ログインボタンのスタイルを修正
- レスポンシブ対応を追加
- 色調整（#3498db → #2980b9）

### 変更ファイル
- \`static/css/main.css\` - ボタンスタイル修正
- \`templates/login.html\` - クラス追加

### デプロイ情報
- サービス: sound-platform
- リージョン: asia-northeast1
- ステータス: 成功

### 確認結果
- スクリーンショット撮影完了
- 期待通りの表示を確認"
```

## Example 2: ユーザーへの質問

**シナリオ**: デプロイ先のサービス名がわからない場合

```bash
cd "C:\Users\Tenormusica\Documents\github-remote-desktop" && python task_complete_private.py "## 確認依頼: デプロイ先サービス名

### 質問内容
現在使用中のCloud Runサービス名を教えてください。

### 理由
複数のサービス（sound-platform, sound-platform-v5等）が存在するため、
正しいサービスへデプロイする必要があります。

### 現在の状況
コード修正は完了しています。デプロイ待ちの状態です。

### 選択肢
1. sound-platform
2. sound-platform-v5
3. その他（具体的なサービス名をお知らせください）"
```

## Example 3: エラー報告

**シナリオ**: デプロイ中にエラーが発生した場合

```bash
cd "C:\Users\Tenormusica\Documents\github-remote-desktop" && python task_complete_private.py "## エラー発生: Cloud Runデプロイ失敗

### エラー内容
\`\`\`
ERROR: (gcloud.run.deploy) PERMISSION_DENIED: Permission denied
\`\`\`

### 発生箇所
Cloud Run デプロイ実行時

### 試みた解決策
1. アカウント再認証 - 効果なし
2. プロジェクト再設定 - 効果なし

### 推奨アクション
以下のいずれかをお願いします:
1. GCPコンソールで権限を確認
2. 別のアカウントでの実行を試す

### 現在の状況
デプロイ待機中"
```

## Example 4: 待機報告

**シナリオ**: ユーザーの追加入力を待つ場合

```bash
cd "C:\Users\Tenormusica\Documents\github-remote-desktop" && python task_complete_private.py "## 待機中: 追加情報待ち

### 待機理由
ログイン認証情報が不明なため、テスト実行を待機しています。

### 必要な情報
- テスト用アカウントのメールアドレス
- パスワード

### 現在の状況
UI修正は完了済み。
動作確認のためのログインテストを待っています。"
```

## Example 5: 情報提供報告

**シナリオ**: コード分析結果を報告する場合

```bash
cd "C:\Users\Tenormusica\Documents\github-remote-desktop" && python task_complete_private.py "## 調査結果: パフォーマンス分析

### 分析対象
\`static/js/app.js\` のパフォーマンス

### 発見事項
1. **重複したイベントリスナー** - 3箇所で発見
2. **未使用のimport** - 5つのモジュールが未使用
3. **N+1クエリ** - データ取得で非効率なパターン

### 推奨対応
1. イベントリスナーの統合（優先度: 高）
2. 未使用importの削除（優先度: 中）
3. クエリの最適化（優先度: 高）

### 次のステップ
修正を開始してよいか確認をお願いします。"
```

## 重要なポイント

### すべての報告に共通するルール

1. **マークダウン形式を使用** - 見出し、リスト、コードブロックを適切に使用
2. **具体的な情報を含める** - ファイル名、コマンド、エラーメッセージなど
3. **次のアクションを明記** - ユーザーが何をすべきかを明確に

### 報告漏れチェックリスト

回答を送信する前に確認:

- [ ] 報告コマンドを実行したか？
- [ ] 報告内容にすべての重要情報が含まれているか？
- [ ] マークダウン形式で記述されているか？
- [ ] 次のステップが明記されているか？
