# Remote Desktop Project - ルールブック

## 🎯 プロジェクト概要

**スマホ→PC画面表示＋テキスト貼り付け**の最小実装プロジェクト
- PC画面をスマホでリアルタイム表示
- スマホからPCのClaude Codeチャット欄にテキスト貼り付け
- 単一インスタンス構成で状態分断を回避

## 📁 ファイル構成

```
web-remote-desktop/
├── app_min.py              # メインサーバー（Cloud Run）
├── client_min.py           # PCクライアント（ローカル実行）
├── requirements_min.txt    # Python依存関係
├── Dockerfile             # Cloud Run用
└── PROJECT_RULES.md       # このファイル
```

## 🔧 技術スタック

- **サーバー**: Flask + Flask-SocketIO + gunicorn
- **スクリーンキャプチャ**: PyAutoGUI + Pillow
- **テキスト貼り付け**: pyperclip（クリップボード経由）
- **通信**: Socket.IO（メイン）+ HTTP（フォールバック）
- **デプロイ**: Google Cloud Run

## ⚙️ システム構成

### Cloud Run設定
- **単一インスタンス必須**: `--max-instances=1 --min-instances=1`
- **メモリ**: 512Mi
- **ポート**: 8080
- **認証**: 不要（`--allow-unauthenticated`）

### 画面解像度
- **キャプチャ解像度**: 元画面の縦横比を保持して1200x675程度
- **JPEG品質**: 50（バランス重視）
- **更新間隔**: 3秒

## 🎮 機能

### 1. PC画面表示
- スマホで https://remote-desktop-2yy4vkcmia-uc.a.run.app にアクセス
- リアルタイムPC画面表示（3秒更新）
- HTTP fallback: `/frame.jpg` で静的画像も取得可能

### 2. テキスト貼り付け
- スマホのテキストエリア→PCのClaude Codeチャット欄
- 自動Enter機能（チェックボックス）
- Ctrl+Enter ショートカット対応

## 🚀 デプロイ手順

```bash
cd "C:\Users\Tenormusica\web-remote-desktop"
"C:\Users\Tenormusica\google-cloud-sdk\bin\gcloud.cmd" run deploy remote-desktop \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 512Mi \
  --max-instances 1 \
  --min-instances 1 \
  --quiet
```

## 🖥️ PCクライアント起動

```bash
cd "C:\Users\Tenormusica\web-remote-desktop"
python client_min.py
```

## ⚠️ 重要ルール

### 1. 単一インスタンス必須
- Cloud Runは必ず `--max-instances=1 --min-instances=1` で設定
- 複数インスタンスは状態分断を引き起こす

### 2. シンプル第一
- 複雑な機能は追加しない
- 最小差分での改良のみ
- 動作する状態を維持

### 3. フォールバック設計
- Socket.IO + HTTP のデュアル通信
- pyperclip + typewrite のデュアル貼り付け
- 確実な動作を優先

## 🔍 トラブルシューティング

### PC画面が表示されない
1. `/health` エンドポイントで状態確認
2. `/frame.jpg` で静的画像確認
3. client_min.py の再起動

### テキスト貼り付けが動かない
1. 「🌐 HTTP Fallback」ボタンを試す
2. pyperclip インストール確認: `pip install pyperclip`
3. Claude Codeウィンドウがアクティブか確認

### 接続が不安定
- Polling transport使用中のため基本的に安定
- プロキシ環境でも動作するよう設計済み

## 📊 成功指標

- ✅ PC画面がスマホで表示される
- ✅ HTTP fallback が 200 OK を返す
- ✅ テキスト貼り付けが動作する
- ✅ 単一インスタンス構成が維持される

## 🎯 達成状況

**✅ Phase 1**: PC画面表示 - 完了
**✅ Phase 2**: テキスト貼り付け - 完了  
**🎉 プロジェクト完了**: 最小機能要件を満たす

---

*Last Updated: 2025-08-27*  
*Project Status: ✅ COMPLETED*