# Claude Voice Hotkey - 詳細設計書

## 📋 プロジェクト概要

**プロジェクト名:** Claude Voice Hotkey  
**対象:** Claude AI Web版 (https://claude.ai/)  
**目的:** マウスサイドボタンでClaude.aiの音声入力を高速制御  
**作成日:** 2025-10-29  
**バージョン:** 1.0

---

## 🎯 主要機能

### 1. マウスサイドボタンによる音声入力制御
- マウスサイドボタン押下 → Claude.aiの音声入力を開始
- ボタンを離す → 音声入力を停止 → 即座に送信
- 既存の音声機能より高速化（ボタン離した瞬間に送信）

### 2. 設定のカスタマイズ
- 機能のON/OFF切り替え
- 使用するマウスボタンの選択（サイドボタン1/2/両方）
- 自動送信のON/OFF切り替え
- Chrome Storage APIで設定を永続化

### 3. 既存機能との統合
- Claude.aiの標準音声入力機能を活用
- 高精度な文字起こしエンジンをそのまま利用
- UIを自動操作して制御

---

## 🏗️ アーキテクチャ

### システム構成

```
┌─────────────────────────────────────────┐
│         Claude AI Web Interface         │
│         (https://claude.ai/)            │
│                                         │
│  ┌─────────────┐    ┌──────────────┐  │
│  │ 音声ボタン   │    │ 送信ボタン    │  │
│  └─────────────┘    └──────────────┘  │
└────────────────┬────────────────────────┘
                 │ 自動クリック
                 ↓
┌─────────────────────────────────────────┐
│          Content Script                  │
│         (content.js)                     │
│                                          │
│  - マウスイベント監視                    │
│  - 音声ボタン自動検出・クリック          │
│  - 送信ボタン自動検出・クリック          │
│  - タイミング制御（500ms待機）           │
└────────────────┬────────────────────────┘
                 │ Chrome Storage API
                 ↓
┌─────────────────────────────────────────┐
│          Popup UI                        │
│     (popup.html/popup.js)                │
│                                          │
│  - 設定画面UI                            │
│  - 設定の読み込み・保存                  │
└─────────────────────────────────────────┘
```

### データフロー

```
1. ユーザーがマウスサイドボタンを押下
   ↓
2. Content Scriptがmousedownイベントを検出
   ↓
3. Chrome Storageから設定を確認
   ↓
4. 音声ボタンを自動検出
   ↓
5. 音声ボタンをクリック → 音声入力開始
   ↓
6. ユーザーが話す
   ↓
7. ユーザーがマウスボタンを離す
   ↓
8. Content Scriptがmouseupイベントを検出
   ↓
9. 音声ボタンを再度クリック → 音声入力停止
   ↓
10. 500ms待機（テキスト変換完了待ち）
   ↓
11. 送信ボタンを自動検出
   ↓
12. 送信ボタンをクリック → メッセージ送信
```

---

## 📁 ファイル構成

```
claude-voice-hotkey/
├── manifest.json          # Chrome拡張機能マニフェスト（Manifest V3）
├── content.js             # コンテントスクリプト（メイン処理）
├── popup.html             # 設定画面UI
├── popup.js               # 設定画面制御
├── icon16.png             # 拡張機能アイコン（16x16）
├── icon48.png             # 拡張機能アイコン（48x48）
├── icon128.png            # 拡張機能アイコン（128x128）
├── README.md              # プロジェクト概要・使用方法
└── DESIGN.md              # 詳細設計書（本ファイル）
```

---

## 🔧 技術仕様

### 1. manifest.json

**Manifest Version:** V3  
**必須パーミッション:**
- `storage` - 設定保存用
- `activeTab` - アクティブタブへのアクセス

**Host Permissions:**
- `https://claude.ai/*` - Claude AIサイトへのアクセス

```json
{
  "manifest_version": 3,
  "name": "Claude Voice Hotkey",
  "version": "1.0",
  "description": "マウスサイドボタンでClaude.aiの音声入力を制御",
  "permissions": ["storage", "activeTab"],
  "host_permissions": ["https://claude.ai/*"],
  "content_scripts": [
    {
      "matches": ["https://claude.ai/*"],
      "js": ["content.js"],
      "run_at": "document_end"
    }
  ],
  "action": {
    "default_popup": "popup.html"
  }
}
```

---

### 2. content.js（コンテントスクリプト）

#### クラス構成

**ClaudeVoiceHotkey**
- シングルトンクラス
- マウスイベント監視・音声入力制御・自動送信の全体制御

#### 主要プロパティ

```javascript
{
  isRecording: false,        // 録音状態フラグ
  voiceButton: null,         // 音声ボタンDOM要素
  settings: {
    enabled: true,           // 機能有効化
    mouseButton: 'side1',    // マウスボタン選択
    autoSend: true           // 自動送信有効化
  }
}
```

#### 主要メソッド

##### `init()`
初期化処理

**処理内容:**
1. Chrome Storageから設定を読み込み
2. 5秒待機（ページ完全ロード待ち）
3. マウスイベント監視を開始

```javascript
async init() {
  await this.loadSettings();
  await this.sleep(5000);
  this.startMouseListener();
}
```

##### `loadSettings()`
設定読み込み

**処理内容:**
- Chrome Storage APIから設定を取得
- デフォルト値を設定

```javascript
async loadSettings() {
  return new Promise((resolve) => {
    chrome.storage.sync.get(['enabled', 'mouseButton', 'autoSend'], (result) => {
      if (result.enabled !== undefined) this.settings.enabled = result.enabled;
      if (result.mouseButton) this.settings.mouseButton = result.mouseButton;
      if (result.autoSend !== undefined) this.settings.autoSend = result.autoSend;
      resolve();
    });
  });
}
```

##### `startMouseListener()`
マウスイベント監視開始

**監視イベント:**
- `mousedown` - ボタン押下
- `mouseup` - ボタン離す

**処理内容:**
```javascript
document.addEventListener('mousedown', (e) => {
  if (this.isTargetMouseButton(e.button) && !this.isRecording) {
    e.preventDefault();
    e.stopPropagation();
    this.startVoiceInput();
  }
}, true);

document.addEventListener('mouseup', (e) => {
  if (this.isTargetMouseButton(e.button) && this.isRecording) {
    e.preventDefault();
    e.stopPropagation();
    this.stopVoiceInput();
  }
}, true);
```

**重要なポイント:**
- `true`パラメータでキャプチャフェーズで実行（優先度高）
- `preventDefault()`/`stopPropagation()`でデフォルト動作を抑制

##### `isTargetMouseButton(button)`
マウスボタン判定

**ボタン番号:**
- Button 3 = サイドボタン1（戻る）
- Button 4 = サイドボタン2（進む）

```javascript
isTargetMouseButton(button) {
  if (this.settings.mouseButton === 'side1') {
    return button === 3;
  } else if (this.settings.mouseButton === 'side2') {
    return button === 4;
  } else if (this.settings.mouseButton === 'both') {
    return button === 3 || button === 4;
  }
  return false;
}
```

##### `startVoiceInput()`
音声入力開始

**処理内容:**
1. `findVoiceButton()`で音声ボタンを検出
2. 音声ボタンをクリック
3. `isRecording`フラグをtrueに設定

```javascript
startVoiceInput() {
  this.voiceButton = this.findVoiceButton();
  if (!this.voiceButton) {
    console.error('❌ 音声入力ボタンが見つかりません');
    return;
  }
  this.voiceButton.click();
  this.isRecording = true;
}
```

##### `stopVoiceInput()`
音声入力停止 → 自動送信

**処理内容:**
1. 音声ボタンを再度クリック（停止）
2. `isRecording`フラグをfalseに設定
3. 500ms待機（テキスト変換完了待ち）
4. `sendMessage()`で自動送信

```javascript
async stopVoiceInput() {
  this.voiceButton.click();
  this.isRecording = false;
  
  if (this.settings.autoSend) {
    await this.sleep(500);
    this.sendMessage();
  }
}
```

**待機時間の根拠:**
- Claude.aiの音声→テキスト変換に約300-500ms必要
- 500ms待機で安定動作を実現

##### `findVoiceButton()`
音声ボタン自動検出

**検出方法:**
1. セレクタパターンマッチング
2. フォールバック: 全buttonを探索

**セレクタパターン:**
```javascript
const selectors = [
  'button[aria-label*="voice"]',
  'button[aria-label*="音声"]',
  'button[aria-label*="Voice"]',
  'button[aria-label*="microphone"]',
  'button[aria-label*="マイク"]',
  'button[data-testid*="voice"]',
  'button[class*="voice"]',
  'button svg[class*="microphone"]',
  'button svg[class*="mic"]'
];
```

**フォールバック検索:**
```javascript
const allButtons = document.querySelectorAll('button');
for (const button of allButtons) {
  const ariaLabel = button.getAttribute('aria-label') || '';
  const title = button.getAttribute('title') || '';
  const text = button.textContent || '';
  
  if (
    ariaLabel.toLowerCase().includes('voice') ||
    ariaLabel.toLowerCase().includes('音声') ||
    // ... 他のキーワード
  ) {
    return button;
  }
}
```

##### `sendMessage()`
メッセージ自動送信

**処理内容:**
1. `findSendButton()`で送信ボタンを検出
2. 送信ボタンをクリック

```javascript
sendMessage() {
  const sendButton = this.findSendButton();
  if (!sendButton) {
    console.error('❌ 送信ボタンが見つかりません');
    return;
  }
  sendButton.click();
}
```

##### `findSendButton()`
送信ボタン自動検出

**セレクタパターン:**
```javascript
const selectors = [
  'button[aria-label*="send"]',
  'button[aria-label*="送信"]',
  'button[aria-label*="Send"]',
  'button[data-testid*="send"]',
  'button[type="submit"]',
  'button svg[class*="send"]',
  'button svg[class*="arrow"]'
];
```

**重要なチェック:**
```javascript
if (!button.disabled) {
  // disabled属性がないことを確認
  return button;
}
```

---

### 3. popup.html/popup.js（設定画面）

#### UI構成

**設定項目:**
1. **機能有効化** - トグルスイッチ
2. **マウスボタン** - ドロップダウン選択
3. **自動送信** - トグルスイッチ
4. **ステータス表示** - 設定保存状態

#### popup.js - 設定管理

**設定読み込み:**
```javascript
chrome.storage.sync.get(['enabled', 'mouseButton', 'autoSend'], (result) => {
  enabledToggle.checked = result.enabled !== undefined ? result.enabled : true;
  mouseButtonSelect.value = result.mouseButton || 'side1';
  autoSendToggle.checked = result.autoSend !== undefined ? result.autoSend : true;
});
```

**設定保存:**
```javascript
function saveSettings() {
  const settings = {
    enabled: enabledToggle.checked,
    mouseButton: mouseButtonSelect.value,
    autoSend: autoSendToggle.checked
  };
  
  chrome.storage.sync.set(settings, () => {
    statusDiv.textContent = '✅ 設定保存完了';
  });
}
```

**リアルタイム保存:**
- 各設定項目に`change`イベントリスナーを設定
- 変更時に即座に保存

---

## ⚙️ 設定・パラメータ

### マウスボタン設定

| 値 | 説明 | Button番号 |
|---|---|---|
| `side1` | サイドボタン1（戻る） | Button 3 |
| `side2` | サイドボタン2（進む） | Button 4 |
| `both` | 両方のサイドボタン | Button 3 or 4 |

### タイミング設定

| パラメータ | 値 | 説明 |
|-----------|---|------|
| 起動待機時間 | 5000ms | ページロード後の監視開始待機 |
| テキスト変換待機 | 500ms | 音声停止後のテキスト変換完了待機 |

### デフォルト設定

| 設定項目 | デフォルト値 | 説明 |
|---------|------------|------|
| enabled | `true` | 機能有効化 |
| mouseButton | `'side1'` | サイドボタン1を使用 |
| autoSend | `true` | 自動送信有効 |

---

## 🔄 処理フロー詳細

### 全体フロー

```
1. 拡張機能インストール
   ↓
2. Claude.aiにアクセス
   ↓
3. content.js自動注入（document_end）
   ↓
4. ClaudeVoiceHotkey初期化
   ├─ 設定読み込み
   ├─ 5秒待機
   └─ マウスイベント監視開始
   ↓
5. ユーザーがマウスサイドボタン押下
   ↓
6. mousedownイベント検出
   ├─ 機能有効化チェック
   ├─ ボタン番号チェック
   └─ 録音中フラグチェック
   ↓
7. 音声ボタン検出
   ├─ セレクタパターンマッチング
   └─ フォールバック検索
   ↓
8. 音声ボタンクリック → 音声入力開始
   ↓
9. ユーザーが話す
   ↓
10. ユーザーがマウスボタン離す
   ↓
11. mouseupイベント検出
   ├─ 機能有効化チェック
   ├─ ボタン番号チェック
   └─ 録音中フラグチェック
   ↓
12. 音声ボタンクリック → 音声入力停止
   ↓
13. 500ms待機
   ↓
14. 送信ボタン検出
   ├─ セレクタパターンマッチング
   └─ フォールバック検索
   ↓
15. 送信ボタンクリック → メッセージ送信
   ↓
16. 完了
```

### エラーハンドリング

**音声ボタンが見つからない場合:**
```javascript
if (!this.voiceButton) {
  console.error('❌ 音声入力ボタンが見つかりません');
  return; // 処理を中断
}
```

**送信ボタンが見つからない場合:**
```javascript
if (!sendButton) {
  console.error('❌ 送信ボタンが見つかりません');
  return; // 処理を中断（音声入力は完了している）
}
```

---

## 🚨 重要な注意事項

### 1. Claude.ai UIの変更に対する対応

**問題:**
- Claude.aiのUIが更新されると、セレクタが変更される可能性がある
- 音声ボタン・送信ボタンが検出できなくなる

**対策:**
- 複数のセレクタパターンを用意
- フォールバック検索を実装
- aria-label、title、textContentなど複数の属性を確認

**メンテナンス:**
- UI更新時はcontent.jsのセレクタパターンを追加

### 2. マウスボタンイベントの優先度

**実装の工夫:**
- イベントリスナーに`true`パラメータを指定（キャプチャフェーズ）
- `preventDefault()`/`stopPropagation()`でデフォルト動作を抑制
- ブラウザのサイドボタンナビゲーション（戻る/進む）を無効化

### 3. テキスト変換待機時間

**待機時間の設定根拠:**
- Claude.aiの音声→テキスト変換に約300-500ms必要
- 500ms待機で安定動作を実現
- 環境によっては調整が必要な場合がある

**カスタマイズ方法:**
```javascript
// content.jsの以下の行を変更
await this.sleep(500); // 500を1000に変更すると1秒待機
```

### 4. Chrome Storage APIの同期

**制限事項:**
- 同期ストレージは最大100KB
- 設定項目は少ないため問題なし

**データ構造:**
```javascript
{
  enabled: true,        // boolean
  mouseButton: 'side1', // string ('side1' | 'side2' | 'both')
  autoSend: true        // boolean
}
```

---

## 🐛 既知の問題・制限事項

### 1. マウスボタンが反応しない

**原因:** マウスのサイドボタンが無効、または別のボタン番号

**対処:**
1. マウスの設定でサイドボタンが有効か確認
2. 設定で「両方のサイドボタン」を選択して試す

### 2. 音声入力が開始されない

**原因:** Claude.aiの音声ボタンが検出できていない

**対処:**
1. F12でコンソールを開く
2. エラーメッセージを確認
3. Claude.aiのUIが更新された可能性 → セレクタを更新

### 3. 自動送信されない

**原因:** 送信ボタンが検出できていない、またはテキスト変換が未完了

**対処:**
1. 設定で「自動送信」がONか確認
2. 500ms待機時間を延長（1000msに変更）

### 4. Message Port Closed Error

**問題:** 稀に "The message port closed before a response was received" エラー

**影響:** 機能には影響なし

**状態:** 監視中

---

## 🧪 テスト方法

### 基本動作確認

1. **拡張機能の読み込み**
   - `chrome://extensions/` を開く
   - 「デベロッパーモード」をON
   - 「パッケージ化されていない拡張機能を読み込む」
   - `claude-voice-hotkey`フォルダを選択

2. **Claude.aiでテスト**
   - `https://claude.ai/new` を開く
   - マウスサイドボタンを押す → 音声入力開始確認
   - ボタンを離す → 音声入力停止 → 自動送信確認

### コンソールログ確認

F12でデベロッパーツールを開き、以下のログを確認：

```
🎤 Claude Voice Hotkey: 初期化開始
⚙️ 設定読み込み完了: {enabled: true, mouseButton: "side1", autoSend: true}
🖱️ マウスリスナー開始
✅ Claude Voice Hotkey: 初期化完了

// マウスボタン押下時
🎤 音声入力開始（マウスボタン押下）
🔍 音声入力ボタン検出: button.voice-button
✅ 音声入力開始

// マウスボタン離す時
🎤 音声入力停止（マウスボタン離す）
✅ 音声入力停止
🔍 送信ボタン検出: button.send-button
✅ メッセージ送信完了
```

### 設定画面のテスト

1. 拡張機能アイコンをクリック
2. 各設定項目を変更
3. 「✅ 設定保存完了」が表示されることを確認
4. Claude.aiで動作確認

---

## 📝 今後の改善案

### 機能追加

**高優先度:**
- [ ] キーボードショートカットでの制御（Ctrl+Shift+Vなど）
- [ ] 音声入力中のビジュアルフィードバック（アイコン変化など）
- [ ] テキスト変換待機時間のカスタマイズUI

**中優先度:**
- [ ] 音声入力履歴の表示
- [ ] ショートカットキーのカスタマイズ
- [ ] 音声入力中の録音レベル表示

**低優先度:**
- [ ] 他のマウスボタン対応（ホイールクリックなど）
- [ ] 音声入力の一時停止機能
- [ ] 複数言語対応（設定画面の多言語化）

### パフォーマンス改善

- [ ] ボタン検出のキャッシュ化（初回検出後はキャッシュを使用）
- [ ] セレクタパターンの優先順位最適化
- [ ] DOM変更時の再検出機能

### UI改善

- [ ] 設定画面のデザイン改善
- [ ] 音声入力状態の通知
- [ ] エラー時のユーザーフレンドリーなメッセージ

---

## 🔗 関連リンク

- **Chrome Extensions Manifest V3:** https://developer.chrome.com/docs/extensions/mv3/
- **Chrome Storage API:** https://developer.chrome.com/docs/extensions/reference/storage/
- **Mouse Events:** https://developer.mozilla.org/en-US/docs/Web/API/MouseEvent

---

## 📄 ライセンス

このプロジェクトは個人利用・学習目的で作成されました。

---

## ✅ チェックリスト（デプロイ前）

- [x] Chrome拡張機能読み込み確認
- [x] Claude.aiでの動作確認
- [x] マウスサイドボタンでの音声入力開始確認
- [x] ボタン離しでの自動送信確認
- [x] コンソールログでエラーなし確認
- [x] 設定画面での設定変更確認
- [x] 設定の永続化確認

---

**最終更新:** 2025-10-29  
**動作確認環境:** Chrome 120+ / Claude AI Web
