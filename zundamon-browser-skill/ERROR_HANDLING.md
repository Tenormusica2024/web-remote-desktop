# エラーハンドリング・トラブルシューティング

このドキュメントでは、Zundamon Voice for Claude拡張機能で発生する可能性のあるエラーと解決方法を記載します。

---

## 目次
1. [VRM WebSocket接続エラー](#vrm-websocket接続エラー)
2. [一般的なトラブルシューティング](#一般的なトラブルシューティング)

---

## VRM WebSocket接続エラー

### 問題現象
VMagicMirrorでVRMの口パクが突然動作しなくなり、ChromeのF12コンソールに以下のエラーが繰り返し表示される：

```javascript
❌ VRM WebSocket Bridgeエラー
WebSocket connection to 'ws://localhost:8765/' failed
🔄 VRM WebSocket Bridge再接続試行中...
```

### 根本原因

#### 1. 重複したpostMessageリスナー（設計上の問題）

**問題のあったコード（vrm-connector.js 226-260行）:**
```javascript
window.addEventListener('message', async (event) => {
  if (event.source !== window) return;  // ❌ CRITICAL ERROR
  // ISOLATED worldからのメッセージを拒否してしまう
});
```

**原因:**
- `event.source !== window`チェックにより、**ISOLATED world（content.js）からのpostMessageを完全拒否**
- Chrome Extension Manifest V3では、ISOLATED world → MAIN worldのpostMessageは`event.source !== window`となる
- このリスナーは一切のメッセージを処理できない**死んだコード**

**正しい実装（vrm-bridge.js）:**
```javascript
window.addEventListener('message', async (event) => {
  // event.sourceチェックなし（ISOLATED worldからのメッセージを受信）
  if (!event.data || typeof event.data !== 'object') return;
  if (type !== 'VRM_BRIDGE') return;
  
  try {
    switch (method) {
      case 'connect':
        if (window.vrmConnector) {
          await window.vrmConnector.connect();
        }
        break;
      // ...
    }
  } catch (error) {
    // エラーハンドリング
  }
});
```

**manifest.jsonのロード順序:**
```json
"js": ["vts-connector.js", "vrm-connector.js", "vrm-bridge.js"]
```
- vrm-bridge.jsが最後にロードされるため、正しいリスナーが登録される
- vrm-connector.jsの誤ったリスナーは実害はなかったが、設計上の問題として削除

#### 2. Bridge Serverプロセスの不完全起動（直接的原因）

**問題:**
- `npm start`でBridge Serverを起動したが、WebSocketサーバー部分が正常に起動していなかった
- OSCメッセージ（Blink）のみ送信され続け、WebSocketサーバーの起動ログが出力されていなかった
- `netstat -ano | findstr :8765`で確認したところ、**ポート8765がLISTEN状態になっていなかった**

**確認方法:**
```powershell
# ポート8765の状態確認
Test-NetConnection -ComputerName localhost -Port 8765
```

**期待される出力:**
```
ComputerName     : localhost
RemotePort       : 8765
TcpTestSucceeded : True
```

### 解決方法

#### ステップ1: Chrome拡張機能の再読み込み
1. `chrome://extensions/`を開く
2. 「Zundamon Voice for Claude」の**再読み込みボタン**をクリック
3. claude.aiページをリフレッシュ

#### ステップ2: Bridge Serverの再起動
```bash
# 既存プロセスを停止
# Ctrl+C または Taskmanagerで node.exe プロセスを終了

# プロジェクトディレクトリに移動
cd "C:\Users\Tenormusica\voicevox-mcp-notification\zundamon-browser-skill"

# Bridge Server起動
npm start
```

**正常起動時のログ:**
```
🚀 VRM WebSocket Bridge Server起動 (WebSocket: 8765, OSC: 39540)
👁️ 自動瞬き開始
✅ OSC Port準備完了
✅ WebSocketクライアント接続  ← Chrome接続成功
📤 ルートTransform送信
🎯 初期化完了: 腕を下げた状態に設定
```

#### ステップ3: 接続確認
Chrome F12コンソールで以下のログを確認：
```javascript
✅ VRM接続成功: this.vrmConnected = true
🎵 VRM初期化: 腕を下げた状態に設定
```

### タイムライン（発生から解決まで）

1. **過去のある時点:** vrm-connector.jsに誤ったpostMessageリスナーを追加（タイムスタンプ: Nov 2 22:26）
2. **動作していた期間:** vrm-bridge.jsの正しいリスナーが機能していたため、口パクは正常動作
3. **突然の停止:** Bridge Serverプロセスが何らかの理由でWebSocketサーバー部分が停止
4. **ユーザーがエラーを報告:** ChromeはWebSocketに接続できず、再接続を繰り返し
5. **調査・修正:** 
   - 重複リスナーを発見・削除（vrm-connector.js:226-260行）
   - Bridge Serverを再起動
   - WebSocket接続成功

### 修正内容

#### 1. vrm-connector.jsの重複リスナー削除
```diff
// 削除前（226-260行）
- // postMessageリスナー（content.jsからのメッセージを受信）
- window.addEventListener('message', async (event) => {
-   // 自分自身からのメッセージのみ受け入れる
-   if (event.source !== window) return;  // ❌ ISOLATED worldを拒否
-   if (!event.data || typeof event.data !== 'object') return;
-   
-   const { type, method, params } = event.data;
-   
-   if (type === 'VRM_BRIDGE') {
-     if (method === 'connect') {
-       // VRM接続試行
-       try {
-         await window.vrmConnector.connect();
-         window.postMessage({
-           type: 'VRM_BRIDGE_RESPONSE',
-           method: 'connect',
-           success: true
-         }, '*');
-       } catch (error) {
-         window.postMessage({
-           type: 'VRM_BRIDGE_RESPONSE',
-           method: 'connect',
-           success: false,
-           error: error.message
-         }, '*');
-       }
-     } else if (method === 'setMouthOpen') {
-       // 口パクパラメータ送信
-       await window.vrmConnector.setMouthOpen(params.value);
-     } else if (method === 'setArmPose') {
-       // 腕ポーズ送信
-       await window.vrmConnector.setArmPose(params.isPlaying);
-     }
-   }
- });

// 削除後（225行まで）: VRMConnectorクラスとインスタンス作成のみ
window.vrmConnector = new VRMConnector();
```

#### 2. Bridge Server再起動
Bridge Serverを完全に停止して再起動することで、WebSocketサーバーが正常に起動。

---

## 一般的なトラブルシューティング

### ポート競合エラー
```
Error: listen EADDRINUSE: address already in use :::8765
```

**解決方法:**
```bash
# Windowsでポート8765を使用しているプロセスを確認
netstat -ano | findstr :8765

# プロセスIDを確認後、強制終了
taskkill /PID [プロセスID] /F
```

### VOICEVOX Engine未起動
```
❌ Background Service Worker応答なし（VOICEVOX Engine起動確認してください）
```

**解決方法:**
1. VOICEVOX Engineを起動（http://localhost:50021）
2. ブラウザで`http://localhost:50021/docs`にアクセスして動作確認

### VMagicMirror接続失敗
```
❌ VRM WebSocket Bridgeエラー
```

**確認項目:**
1. VMagicMirrorが起動しているか
2. VMagicMirrorの設定で「外部トラッキング（VMCプロトコル）を受信」が有効か
3. ポート39540が開いているか

---

## 教訓

1. **ISOLATED/MAIN world間のpostMessage通信では`event.source`チェックを行わない**
   - Chrome Extension Manifest V3では、異なる実行コンテキスト間の通信で`event.source`が異なる
   - データ型チェックとメッセージタイプチェックのみで十分

2. **重複リスナーは設計上の問題であり、早期に削除すべき**
   - 実害がなくても、コードの保守性が低下する
   - 将来的なバグの原因となる可能性がある

3. **長時間実行プロセスは定期的な再起動が必要な場合がある**
   - Node.jsプロセスが不完全な状態で動作していることがある
   - 定期的な再起動で安定性を向上

4. **エラー調査時はログの最初の部分（起動ログ）を必ず確認する**
   - プロセスが正常に起動しているかの確認は最優先
   - ポートのLISTEN状態を確認することが重要

---

## 参考資料

- [Chrome Extension Manifest V3 - Content Scripts](https://developer.chrome.com/docs/extensions/mv3/content_scripts/)
- [VMC Protocol Specification](https://protocol.vmc.info/)
- [WebSocket API - MDN](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
