# Zundamon Voice for Claude (Claude Web版) - 詳細設計書

## 📋 プロジェクト概要

**プロジェクト名:** Zundamon Voice for Claude (Browser Extension)  
**対象:** Claude AI Web版 (https://claude.ai/)  
**目的:** Claude AIの応答を検出し、ずんだもん音声で自動読み上げ + Live2D/VRM口パク連携  
**作成日:** 2025-10-28  
**最終更新:** 2025-01-02  
**バージョン:** 1.1.0

---

## 🎯 主要機能

### 1. Claude応答の自動検出
- Claude AIのチャット画面でClaudeの応答を自動検出
- ユーザーメッセージとClaude応答を区別
- ストリーミング完了を待機してから処理

### 2. 音声読み上げ
- VOICEVOXエンジンを使用したずんだもん音声合成
- Speaker ID 3（ずんだもん ノーマル）
- 自動再生・キュー管理で重複再生防止

### 3. テキストフィルタリング
- 思考プロセスブロックの除外
- コードブロック・ツール実行結果の除外
- UIボタンテキストの除外

### 4. VTubeStudio Live2D口パク連携（v1.1.0）
- WebSocket API経由でVTubeStudioと通信（localhost:8001）
- リアルタイム音量解析による口パクアニメーション
- 自動認証・トークン管理
- 自動再接続機能（5秒インターバル）

### 5. VRM連携機能（v1.1.0）
- VMC Protocol経由でVRMモデルと連携（VSeeFace等）
- WebSocket Bridge Server（Node.js）経由でOSC通信
- ISOLATED/MAIN World通信ブリッジ実装
- アニメ風口パクアルゴリズム（8フレームごとに開閉切り替え）

### 6. パフォーマンス最適化（v1.0.0-v1.1.0）
- 並列プリフェッチ（最大5チャンク同時）
- 最初のメッセージまで約0.5-1.5秒（従来比2秒短縮）
- チャンク間待機時間ほぼゼロ（キャッシュヒット時）

---

## 🏗️ アーキテクチャ

### コンポーネント構成

```
┌─────────────────────────────────────────────────────────────┐
│              Claude AI Web Interface                        │
│              (https://claude.ai/)                           │
└──────────────────┬──────────────────────────────────────────┘
                   │ DOM Mutation
                   ↓
┌────────────────────────────────────────────────────────────┐
│         Content Script (ISOLATED World)                    │
│              (content.js)                                  │
│                                                            │
│  - MutationObserver監視                                   │
│  - 応答検出・テキスト抽出                                  │
│  - 並列プリフェッチ（最大5チャンク）                       │
│  - 音声再生 + 音量解析                                     │
└──────┬─────────────────────────────────┬─────────────────┘
       │ chrome.runtime.sendMessage       │ postMessage
       ↓                                  ↓
┌─────────────────────────┐  ┌──────────────────────────────┐
│  Background Service     │  │  MAIN World Script            │
│  Worker                 │  │  (vts-connector.js,           │
│  (background.js)        │  │   vrm-connector.js,           │
│                         │  │   vrm-bridge.js)              │
│  - CORS回避プロキシ     │  │                               │
│  - VOICEVOX API呼び出し │  │  - VTubeStudio WebSocket連携 │
│  - ping/pong機構        │  │  - VRM VMC Protocol連携      │
└────────┬────────────────┘  │  - postMessageリレー         │
         │                    └──────┬───────────────────────┘
         │ HTTP Request              │ WebSocket/OSC
         ↓                           ↓
┌─────────────────────┐    ┌─────────────────────────────┐
│  VOICEVOX Engine    │    │  VTubeStudio / VSeeFace    │
│  (localhost:50021)  │    │  (localhost:8001/39540)    │
│                     │    │                             │
│  - 音声クエリ生成   │    │  - Live2D口パク制御        │
│  - 音声合成         │    │  - VRM口パク制御           │
└─────────────────────┘    └─────────────────────────────┘
         ↓
┌─────────────────────┐
│  WebSocket Bridge   │
│  Server (Node.js)   │
│  (localhost:8765)   │
│                     │
│  - WebSocket受信    │
│  - OSC送信          │
└─────────────────────┘
```

---

## 📁 ファイル構成

```
zundamon-browser-skill/
├── manifest.json          # Chrome拡張機能マニフェスト（Manifest V3）
├── content.js             # コンテントスクリプト（ISOLATED World）
├── vts-connector.js       # VTubeStudio WebSocket連携（MAIN World）
├── vrm-connector.js       # VRM VMC Protocol連携（MAIN World）
├── vrm-bridge.js          # ISOLATED/MAIN World通信ブリッジ（MAIN World）
├── background.js          # バックグラウンドサービスワーカー
├── bridge-server.js       # WebSocket-OSC Bridge Server（Node.js）
├── popup.html             # 拡張機能ポップアップUI
├── popup.js               # ポップアップUI制御
├── package.json           # Node.js依存関係（ws, osc）
├── icon16.png             # 拡張機能アイコン（16x16）
├── icon48.png             # 拡張機能アイコン（48x48）
├── icon128.png            # 拡張機能アイコン（128x128）
├── README.md              # プロジェクト概要・インストール手順
└── CLAUDE_WEB_VERSION_DESIGN.md  # 本ファイル（詳細設計書）
```

---

## 🔧 技術仕様

### 1. manifest.json

**Manifest Version:** V3  
**必須パーミッション:**
- `storage` - 設定保存用
- `webRequest` - リクエスト監視用

**Host Permissions:**
- `https://claude.ai/*` - Claude AIサイトへのアクセス
- `http://localhost:50021/*` - VOICEVOX APIへのアクセス

**Content Scripts:**
- **MAIN World**: `vts-connector.js`, `vrm-connector.js`, `vrm-bridge.js`
  - ページの`window`オブジェクトに直接アクセス可能
  - VTubeStudio/VRM連携の実装
- **ISOLATED World**: `content.js`
  - Chrome拡張機能APIにアクセス可能
  - VOICEVOX音声合成・再生制御

```json
{
  "manifest_version": 3,
  "name": "Zundamon Voice for Claude",
  "version": "1.0.0",
  "description": "Claude AIの応答をずんだもん音声で読み上げるChrome拡張機能",
  "permissions": ["storage", "webRequest"],
  "host_permissions": [
    "https://claude.ai/*",
    "http://localhost:50021/*"
  ],
  "content_scripts": [
    {
      "matches": ["https://claude.ai/*"],
      "js": ["vts-connector.js", "vrm-connector.js", "vrm-bridge.js"],
      "run_at": "document_end",
      "world": "MAIN"
    },
    {
      "matches": ["https://claude.ai/*"],
      "js": ["content.js"],
      "run_at": "document_end"
    }
  ],
  "background": {
    "service_worker": "background.js"
  },
  "action": {
    "default_popup": "popup.html",
    "default_icon": {
      "16": "icon16.png",
      "48": "icon48.png",
      "128": "icon128.png"
    }
  }
}
```

---

### 2. content.js（コンテントスクリプト）

#### クラス構成

**ZundamonVoiceController**
- シングルトンクラス
- Claude応答の監視・検出・音声合成の全体制御

#### 主要メソッド

##### `init()`
- 設定読み込み
- Audio Context初期化
- 5秒待機後に監視開始（既存メッセージの誤検出防止）

##### `startObserving()`
- MutationObserverを起動
- DOM要素の追加を監視

##### `checkForClaudeResponse(element)`
- 追加された要素がClaude応答かチェック
- セレクタ: `[data-is-streaming]`, `[data-test-render-count]`, `.font-claude-message`
- ユーザーメッセージを除外
- ストリーミング状態を確認

##### `waitForStreamingComplete(element)`
- `data-is-streaming`属性の変化を監視
- `false`になるまで待機
- 完了後500ms待機してからテキスト処理
- 10秒タイムアウト（安全装置）

##### `processClaudeMessage(element)`
- WeakSetで処理済み要素をトラッキング
- テキスト抽出・要約・音声合成を実行

##### `extractText(element)`
**除外要素:**
- `pre`, `code` - コードブロック
- `button` - UIボタン
- `[class*="tool"]` - ツール実行結果
- `[class*="thinking"]` - 思考プロセス

**フィルタリングパターン:**
```javascript
// 思考プロセス削除
text = text.replace(/考え中[\s\S]*?(?=[ぁ-んァ-ヶー][ぁ-んァ-ヶーー一-龠]{2,})/g, '');
text = text.replace(/ユーザー[がはに].+?(?=そうですね|はい|いいえ|ありがとう|わかりました|こんにちは|こんばんは|おはよう|では|それでは)/gs, '');

// 個別削除パターン
/ユーザーは.+?[。\.]/g
/ユーザーが.+?[。\.]/g
/これは.+?[。\.]/g
/それは.+?[。\.]/g
/.+?と返答しました[。\.]?/g
/.+?のようです[。\.]?/g
/何か具体的な.+?[。\.]/g
/無理に.+?[。\.]/g
```

**検証:**
- 日本語を含むかチェック
- 3文字未満は除外
- 空文字は除外

##### `summarizeIfNeeded(text)`
- 100文字以内なら全文
- 100文字超なら最初の文のみ
- 最初の文も100文字超なら97文字+「...」

##### `speakText(text)`
- キューベースの音声再生管理
- `isPlaying`フラグで同時再生防止
- Background Service Worker経由で音声合成

##### `synthesizeViaBackground(text)`
- `chrome.runtime.sendMessage`でBackground Service Workerに依頼
- アクション: `synthesize`
- パラメータ: `text`, `speakerID`

##### `playAudio(arrayBuffer)`
- Web Audio APIで再生
- AudioBuffer生成・デコード
- Promise型で再生完了を待機
- **VTubeStudio/VRM連携時**: AnalyserNode生成・音量解析
- **口パクアニメーション**: `animateMouth()`でリアルタイム制御

---

### 3. vts-connector.js（VTubeStudio連携 - MAIN World）

**VTubeStudioConnector クラス**
- VTubeStudio WebSocket API（localhost:8001）との通信を管理

**主要メソッド:**

##### `connect()`
- WebSocket接続確立
- 自動認証（トークン管理 - localStorage）
- 接続失敗時の自動再接続（5秒インターバル）

##### `setMouthOpen(value)`
- `VoiceVolumePlusWhisperVolume`パラメータを制御
- 値の範囲: 0.0（閉じる）～ 1.0（開く）

---

### 4. vrm-connector.js（VRM連携 - MAIN World）

**VRMConnector クラス**
- VRM VMC Protocol（VSeeFace等）との通信を管理
- WebSocket Bridge Server（localhost:8765）経由でOSC送信

**主要メソッド:**

##### `connect()`
- WebSocket接続確立（Bridge Server）
- 接続失敗時の自動再接続（5秒インターバル）

##### `setMouthOpen(value)`
- アニメ風口パクアルゴリズム
- 音声検出時: 8フレーム（約133ms）ごとに「大きく開く(0.8)」と「小さく開く(0.2)」を交互切り替え
- 無音時: 完全に口を閉じる（閾値8）
- 人の声帯域（80Hz-3.5kHz）を重視した音量解析

---

### 5. vrm-bridge.js（ISOLATED/MAIN World通信ブリッジ - MAIN World）

**役割:**
- ISOLATED world（content.js）とMAIN world（vrm-connector.js）間のpostMessage通信を仲介

**イベントハンドラ:**
```javascript
window.addEventListener('message', (event) => {
  // ISOLATED worldからのメッセージを受信
  if (event.data.type === 'VRM_CHECK_CONNECTION') {
    // VRMConnectorに問い合わせ
    const connected = window.vrmConnector?.isConnected;
    window.postMessage({ 
      type: 'VRM_CONNECTION_RESPONSE', 
      connected 
    }, '*');
  }
});
```

---

### 6. bridge-server.js（WebSocket-OSC Bridge Server - Node.js）

**役割:**
- WebSocket（ブラウザ拡張機能）とOSC（VSeeFace等）の通信を橋渡し

**主要機能:**
- WebSocket Server（localhost:8765）でブラウザからのメッセージを受信
- OSC Client（localhost:39540）でVMC Protocolメッセージを送信
- `/VMC/Ext/Blend/Val`アドレスで口パクパラメータを制御

**依存パッケージ:**
- `ws`: WebSocketサーバー実装
- `osc`: OSCプロトコル実装

---

### 7. background.js（バックグラウンドサービスワーカー）

#### 役割
- CORS制約を回避してVOICEVOX APIを呼び出し
- Content Scriptからのメッセージを受信
- **ping/pong機構**でService Workerのスリープを防止（v1.1.0）

#### メッセージハンドラ

**アクション: `ping`（v1.1.0追加）**
```javascript
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'ping') {
    sendResponse({ success: true });
    return true;
  }
});
```

**アクション: `synthesize`**
```javascript
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'synthesize') {
    synthesizeAudio(request.text, request.speakerID)
      .then(audioData => {
        sendResponse({ success: true, audioData: audioData });
      })
      .catch(error => {
        sendResponse({ success: false, error: error.message });
      });
    return true; // 非同期レスポンス
  }
});
```

**Service Worker Sleep対策（v1.1.0）:**
- Chrome MV3のService Workerは非アクティブ時にスリープ
- `synthesize`呼び出し前に`ping`を送信してウェイクアップ
- タイムアウト時間: 25秒 → 10秒に短縮
- リトライ回数: 1回 → 2回に拡大

#### `synthesizeAudio(text, speakerID)`

**ステップ1: 音声クエリ生成**
```javascript
const queryUrl = `${voicevoxAPI}/audio_query?text=${encodeURIComponent(text)}&speaker=${speakerID}`;
const queryResponse = await fetch(queryUrl, { method: 'POST' });
const audioQuery = await queryResponse.json();
```

**ステップ2: 音声合成**
```javascript
const synthesisUrl = `${voicevoxAPI}/synthesis?speaker=${speakerID}`;
const synthesisResponse = await fetch(synthesisUrl, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(audioQuery)
});
const audioBuffer = await synthesisResponse.arrayBuffer();
```

**ステップ3: データ変換**
```javascript
// ArrayBufferをArrayに変換（メッセージング用）
return Array.from(new Uint8Array(audioBuffer));
```

---

## 🔄 処理フロー

### 全体フロー

```
1. ページロード
   ↓
2. 5秒待機（既存メッセージの誤検出防止）
   ↓
3. MutationObserver開始
   ↓
4. DOM要素追加検出
   ↓
5. Claude応答かチェック
   ├─ ユーザーメッセージ → スキップ
   └─ Claude応答 → 次へ
   ↓
6. ストリーミング状態確認
   ├─ ストリーミング中 → 完了待機
   └─ 完了済み → 次へ
   ↓
7. 500ms待機（DOM完全更新保証）
   ↓
8. テキスト抽出・フィルタリング
   ↓
9. 空文字・重複チェック
   ├─ 空/重複 → スキップ
   └─ 有効 → 次へ
   ↓
10. 要約（必要時）
   ↓
11. キュー確認
   ├─ 再生中 → キューに追加
   └─ 空き → 即座実行
   ↓
12. Background Service Workerへメッセージ送信
   ↓
13. VOICEVOX API呼び出し
   ├─ audio_query生成
   └─ synthesis実行
   ↓
14. 音声データ取得
   ↓
15. Web Audio APIで再生
   ↓
16. 再生完了
   ↓
17. キュー確認
   ├─ 残あり → 次を再生（500ms待機後）
   └─ 空 → 待機状態
```

### ストリーミング完了待機フロー

```
1. data-is-streaming="true" 検出
   ↓
2. MutationObserver起動（属性監視）
   ↓
3. data-is-streaming変化待ち
   ├─ 10秒経過 → タイムアウト強制処理
   └─ false検出 → 次へ
   ↓
4. 500ms待機
   ↓
5. テキスト処理開始
```

---

## ⚙️ 設定・パラメータ

### VOICEVOX設定

| パラメータ | 値 | 説明 |
|-----------|---|------|
| API URL | `http://localhost:50021` | VOICEVOX Engine起動先 |
| Speaker ID | `3` | ずんだもん ノーマル |

### タイミング設定

| パラメータ | 値 | 説明 |
|-----------|---|------|
| 起動待機時間 | 5000ms | ページロード後の監視開始待機 |
| ストリーミング完了待機 | 500ms | DOM完全更新待機 |
| ストリーミングタイムアウト | 10000ms | 強制処理までの最大待機時間 |
| キュー間隔 | 500ms | 連続再生時の間隔 |

### テキスト設定

| パラメータ | 値 | 説明 |
|-----------|---|------|
| 最大文字数 | 100文字 | 超過時は要約 |
| 最小文字数 | 3文字 | 未満は除外 |

---

## 🚨 重要な注意事項

### 1. Extended Thinking（拡張思考）モードの制限

**問題:**
- Claude AIの「じっくり考える」（Extended thinking）モードがONの場合、思考プロセステキストが大量に表示される
- 思考プロセスを完全にフィルタリングするのは困難

**解決策:**
- **「じっくり考える」トグルをOFF**にする
- 設定場所: チャット画面左下「Search and tools」ボタン → 「じっくり考える」トグル

**推奨設定:**
```
じっくり考える: OFF（灰色）
```

この設定により：
- ✅ 思考プロセステキストがDOM上に一切表示されない
- ✅ 拡張機能のフィルタリングが不要
- ✅ 実際の応答のみが確実に読み上げられる

### 2. VOICEVOX Engineの起動

**必須:**
- VOICEVOX Engineが `http://localhost:50021` で起動している必要がある
- 起動していない場合、音声合成は失敗するが拡張機能はエラーを無視して動作継続

**起動方法:**
1. VOICEVOX Engineをダウンロード・インストール
2. アプリケーションを起動
3. 自動的にポート50021でAPIサーバーが起動

### 3. CORS制約

**理由:**
- Content ScriptからVOICEVOX APIを直接呼び出すとCORSエラー
- Background Service Workerはhost_permissionsによりCORS制約を回避可能

**対策:**
- Background Service Worker経由でAPI呼び出し
- `chrome.runtime.sendMessage`でプロキシ

### 4. WeakSetによる処理済み管理

**理由:**
- 同じDOM要素が複数回検出される可能性がある
- 重複処理を防止する必要がある

**実装:**
```javascript
this.processedElements = new WeakSet();

// 処理済みチェック
if (this.processedElements.has(element)) {
  return;
}
this.processedElements.add(element);
```

**メリット:**
- メモリリーク防止（DOM要素がGCされたら自動削除）
- 高速なO(1)ルックアップ

---

## 🐛 既知の問題・制限事項（解決済み含む）

### 1. ストリーミング中の誤検出
**問題:** ストリーミング完了前に処理すると「考え中...」のみが抽出される  
**対策:** `waitForStreamingComplete()`で完了待機  
**状態:** ✅ 解決済み（v0.9.0）

### 2. Message Port Closed Error（Service Worker Sleep問題）
**問題:** "The message port closed before a response was received" エラー  
**原因:** Chrome MV3のService Workerが非アクティブ時にスリープ  
**対策:** ping/pong機構で事前ウェイクアップ（v1.1.0）  
**状態:** ✅ 解決済み（v1.1.0）

### 3. タイムアウト後の重複処理
**問題:** 10秒タイムアウト後に処理、その後ストリーミング完了でも処理  
**対策:** WeakSetで重複処理をスキップ  
**状態:** ✅ 解決済み（v0.9.0）

### 4. VRM口パクが動作しない（ISOLATED/MAIN World問題）
**問題:** Content ScriptはISOLATED worldで動作し、ページの`window`オブジェクトにアクセスできない  
**症状:** `window.vrmConnector.isConnected`が常にundefinedで口パク未動作  
**対策:** postMessageブリッジ（vrm-bridge.js）で通信を仲介（v1.1.0）  
**状態:** ✅ 解決済み（v1.1.0）

### 5. Extension Context Invalidation
**問題:** 拡張機能再読み込み時にContent Scriptが無効化され、大量のエラー  
**対策:** `chrome.runtime.id`で無効化検出、`fatal`フラグで静かに終了（v1.1.0）  
**状態:** ✅ 解決済み（v1.1.0）

---

## 🧪 テスト方法

### 基本動作確認

1. **拡張機能の読み込み**
   - `chrome://extensions/` を開く
   - 「デベロッパーモード」をON
   - 「パッケージ化されていない拡張機能を読み込む」
   - `zundamon-browser-skill`フォルダを選択

2. **VOICEVOX Engine起動**
   - VOICEVOX Engineを起動
   - `http://localhost:50021` で動作確認

3. **Claude AIでテスト**
   - `https://claude.ai/new` を開く
   - 「じっくり考える」トグルをOFFに設定
   - 「こんにちは」などのメッセージを送信
   - Claude応答完了後、音声が再生されることを確認

### コンソールログ確認

F12でデベロッパーツールを開き、以下のログを確認：

```
✅ Claude応答の監視を開始しました
🔍 Claude応答を検出: [クラス名]
✅ ストリーミング完了を検出
📝 extractText: 初期テキスト: [テキスト]
🧹 extractText: 思考ブロック削除後: [テキスト]
✅ extractText: 最終テキスト: [テキスト]
🔍 抽出されたテキスト: "[テキスト]"
📝 要約後のテキスト: [文字数] 文字
🗣️ 読み上げ開始: [テキスト]
🔊 音声合成開始: [テキスト]
✅ 音声再生完了
```

### エラーケースのテスト

1. **VOICEVOX未起動**
   - 音声合成エラーがコンソールに表示されるが、拡張機能は動作継続

2. **思考プロセス表示（じっくり考える=ON）**
   - 思考プロセステキストが一部読み上げられる可能性
   - OFFに設定することを推奨

3. **長文応答**
   - 100文字超の場合、最初の文のみが読み上げられる

---

## 📝 開発履歴

### v1.1.0 (2025-01-02) - VRM連携機能追加
- ✅ VRM連携機能実装（VSeeFace対応）
- ✅ VMC Protocol経由でVRMモデル制御
- ✅ WebSocket Bridge Server（Node.js）実装
- ✅ ISOLATED/MAIN World通信ブリッジ実装
- ✅ アニメ風口パクアルゴリズム実装
- ✅ Background Service Worker最適化（ping/pong）
- ✅ Chrome Extension ISOLATED/MAIN World問題解決
- ✅ postMessage event.source検証問題解決
- ✅ Background Service Worker sleep問題解決
- ✅ Extension context invalidation処理実装

### v1.0.0 (2025-01-01) - パフォーマンス最適化
- ✅ 最初のメッセージ待機時間の大幅短縮（約2秒短縮）
- ✅ VTubeStudio Live2D口パク連携機能実装
- ✅ 並列プリフェッチ拡大（3チャンク → 5チャンク）
- ✅ チャンク間待機時間の大幅短縮
- ✅ エラーハンドリング改善

### v0.9.0 (2024-12-27) - 初期バージョン
- ✅ 基本的な音声読み上げ機能実装
- ✅ VOICEVOX API連携
- ✅ Claude応答検出（MutationObserver）
- ✅ 自動音声合成・再生

---

## 📝 今後の改善案

### 機能追加
- [ ] 音声速度調整機能
- [ ] 他のVOICEVOXキャラクターの選択
- [ ] 読み上げ範囲の設定（全文/要約/最初の文）
- [ ] 読み上げON/OFF切り替えショートカットキー
- [ ] 他のVRM対応ソフト連携（Warudo, 3tene等）

### パフォーマンス改善
- [ ] 頻出フレーズの事前合成キャッシュ
- [ ] テキスト抽出処理の最適化

### UI改善
- [ ] ポップアップでのキャラクター選択UI
- [ ] 音声速度スライダー
- [ ] 読み上げ履歴表示
- [ ] VTubeStudio/VRM接続状態の詳細表示

---

## 🔗 関連リンク

- **VOICEVOX Engine:** https://voicevox.hiroshiba.jp/
- **VTubeStudio:** https://denchisoft.com/
- **VTubeStudio API:** https://github.com/DenchiSoft/VTubeStudio
- **VSeeFace:** https://www.vseeface.icu/
- **VMC Protocol:** https://protocol.vmc.info/
- **Chrome Extensions Manifest V3:** https://developer.chrome.com/docs/extensions/mv3/
- **Web Audio API:** https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API
- **postMessage API:** https://developer.mozilla.org/en-US/docs/Web/API/Window/postMessage

---

## 📄 ライセンス

このプロジェクトは個人利用・学習目的で作成されました。  
VOICEVOX Engineの利用規約に従ってください。

---

## ✅ チェックリスト（デプロイ前）

### 基本機能
- [x] VOICEVOX Engine起動確認
- [x] Chrome拡張機能読み込み確認
- [x] Claude AIでの動作確認
- [x] 「じっくり考える」トグルOFF確認
- [x] コンソールログでエラーなし確認
- [x] 音声再生動作確認
- [x] 重複再生防止動作確認
- [x] ストリーミング完了待機動作確認

### VTubeStudio連携（v1.0.0+）
- [x] VTubeStudio起動・モデルロード確認
- [x] WebSocket接続確認（localhost:8001）
- [x] 認証トークン取得確認
- [x] 口パクアニメーション動作確認
- [x] 音声同期精度確認

### VRM連携（v1.1.0+）
- [x] VSeeFace起動・VRMモデルロード確認
- [x] Bridge Server起動確認（npm start）
- [x] WebSocket接続確認（localhost:8765）
- [x] OSC通信確認（localhost:39540）
- [x] アニメ風口パク動作確認
- [x] ISOLATED/MAIN World通信確認

---

**最終更新:** 2025-01-02  
**動作確認環境:** Chrome 120+ / Claude AI Web / VOICEVOX Engine 0.14+ / VTubeStudio / VSeeFace
