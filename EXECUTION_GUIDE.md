# 🚀 システム実行ガイド

## 📋 準備完了状況
✅ **GitHub Issue #3**: 作成済み  
✅ **リモート制御スクリプト**: gh_issue_to_claude_paste.py  
✅ **環境設定**: 完了  
✅ **処理待ちコメント**: 1件待機中  

---

## 🎯 実行手順

### **STEP 1: Claude Codeを準備**
1. **Claude Codeアプリ**を開いてください
2. **右上と右下の入力欄が見える状態**にしてください
3. ウィンドウサイズ・位置を固定してください

### **STEP 2: キャリブレーション実行**
```bash
C:\Users\Tenormusica\cc-snap-to-github\calibrate_system.bat
```

**手順**:
1. バッチファイルをダブルクリック
2. 「右上入力欄にマウスを置いてEnter」の指示に従う
3. 「右下入力欄にマウスを置いてEnter」の指示に従う
4. 座標が自動保存される

### **STEP 3: システム開始**
```bash
C:\Users\Tenormusica\cc-snap-to-github\start_remote_system.bat
```

**手順**:
1. バッチファイルをダブルクリック
2. システム起動メッセージを確認
3. **コンソール画面はそのまま開いたままにしてください**

---

## 🔍 動作確認

### **即座に確認できること**
システム起動後、**約5秒以内**に以下のメッセージがClaude Codeの**下部ペイン**に自動で表示されるはずです：

```
Claude Codeの使い方を教えて（下部ペインに送信）
```

これが表示されれば**システム正常動作**です！

### **追加テスト**
GitHub Issue #3 (https://github.com/Tenormusica2024/web-remote-desktop/issues/3) に以下のコメントを投稿してテスト：

#### 右上ペインテスト
```
upper: 右上ペインのテストメッセージです
```

#### 右下ペインテスト  
```
lower: 右下ペインのテストメッセージです
```

#### Enterなしテスト
```
noenter: upper: 貼り付けのみで手動Enter
```

---

## 🎛️ システム仕様

- **監視間隔**: 5秒
- **対象Issue**: #3 (Claude Code Remote Control Commands)
- **処理ユーザー**: Tenormusica2024のみ
- **自動Enter**: デフォルト有効（`noenter:`で無効化）

---

## 🛠️ トラブルシューティング

### **座標がずれる場合**
```bash
calibrate_system.bat
```
を再実行して座標を再設定

### **システムが反応しない場合**
1. コンソール画面でエラーメッセージを確認
2. Claude Codeが前面に表示されているか確認
3. GitHub Issue #3でコメントの書式を確認

### **動作ログを確認したい場合**
コンソール画面に以下のようなメッセージが表示されます：
```
[15:30:45] comment #1234567 by @Tenormusica2024 -> pane=upper, 25 chars, Enter
  -> pasted and sent (Enter pressed)
```

---

## 📞 成功確認

以下が確認できればシステム完成です：
- ✅ Issue #3のコメントがClaude Codeに自動送信される
- ✅ `upper:`/`lower:`の書式で送信先を制御できる  
- ✅ 日本語と英語の混在テキストが正常に処理される
- ✅ `noenter:`プレフィックスでEnter制御ができる

---

## 🎉 完了！

**これで完全なリモート制御システムが稼働します！**

GitHub Issue経由でどこからでもClaude Codeを操作可能になりました。