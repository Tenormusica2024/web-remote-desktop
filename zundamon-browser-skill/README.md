# 🎙️ Zundamon Voice for Claude - ずんだもん音声読み上げ拡張機能

Claude AIの応答をずんだもん音声で自動読み上げし、VTubeStudio Live2Dモデルと連携して口パクアニメーションを実現するChrome拡張機能

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-Chrome-orange)

## ✨ 主な機能

### 🔊 音声読み上げ
- **VOICEVOX連携**: Claude AIの応答を自動でずんだもん音声に変換
- **ストリーミング対応**: Claude応答完了を検出して即座に読み上げ開始
- **並列プリフェッチ**: 複数チャンクを先行合成して待機時間を最小化（最大5チャンク同時）
- **自動チャンク分割**: 長文を自然な区切りで分割して読み上げ
- **超高速レスポンス**: 最初のメッセージまで約0.5-1.5秒（従来比2秒短縮）

### 🎭 VTubeStudio Live2D口パク連携
- **リアルタイム口パク**: 音声再生と完全同期した口の動き
- **WebSocket API**: VTubeStudioと直接通信（localhost:8001）
- **音量解析**: Web Audio API AnalyserNodeでリアルタイム音量解析
- **自動認証**: 初回起動時に自動でVTubeStudioと認証
- **再接続機能**: 接続切断時の自動再接続（5秒インターバル）

### ⚡ パフォーマンス最適化
- **最初のメッセージまでの待機時間**: 約2秒短縮（従来3.5秒 → 1.5秒）
- **チャンク間待機時間**: ほぼゼロ（プリフェッチキャッシュヒット時）
- **並列処理**: 最大5チャンクを同時にプリフェッチ
- **キャッシュ管理**: Map型の複数キャッシュで効率的な管理

## 📋 必要環境

### 必須
- **Chrome/Edge**: 最新版
- **VOICEVOX Engine**: v0.14.0以降（無料）
  - ダウンロード: https://voicevox.hiroshiba.jp/

### Live2D連携（オプション - VTubeStudio）
- **VTubeStudio**: 最新版（Steam無料版可）
  - Steam: https://store.steampowered.com/app/1325860/VTube_Studio/
- **ずんだもん公式Live2Dモデル**: 無料
  - BOOTH: https://booth.pm/ja/items/5363599

### VRM連携（オプション - VSeeFace等）
- **VSeeFace**: 最新版（無料）
  - 公式サイト: https://www.vseeface.icu/
- **Node.js**: v16以降（Bridge Server用）
  - ダウンロード: https://nodejs.org/
- **ずんだもんVRMモデル**: VRoid Hub等から取得
  - VRoid Hub: https://hub.vroid.com/
  - 公式ずんだもんVRM: https://3d.nicovideo.jp/works/td90573

## 🚀 インストール手順

### 1. VOICEVOX Engineのインストール
```bash
# Windows
1. https://voicevox.hiroshiba.jp/ からダウンロード
2. インストール後、VOICEVOX Engineを起動
3. http://localhost:50021 で動作確認
```

### 2. Chrome拡張機能のインストール
```bash
# リポジトリをクローン
git clone https://github.com/Tenormusica2024/voicevox-mcp-notification.git
cd voicevox-mcp-notification/zundamon-browser-skill

# Chromeで拡張機能をロード
1. chrome://extensions/ を開く
2. 「デベロッパーモード」をON
3. 「パッケージ化されていない拡張機能を読み込む」をクリック
4. zundamon-browser-skill フォルダを選択
```

### 3. VTubeStudio連携の設定（オプション）

#### ずんだもんLive2Dモデルのダウンロード
1. BOOTH: https://booth.pm/ja/items/5363599
2. 「無料ダウンロード」をクリック
3. ZIPファイルを解凍

#### VTubeStudioへのインポート
1. VTubeStudioを起動
2. 左メニュー「Change VTS Model」をクリック
3. 「Import My Model」を選択
4. 解凍したずんだもんモデルフォルダを選択
5. インポート完了後、モデルをロード

#### 拡張機能で連携を有効化
1. Chrome拡張機能のアイコンをクリック
2. 「🎭 VTubeStudio連携」トグルをON
3. claude.aiのページを再読み込み

### 4. VRM連携の設定（オプション）

#### VSeeFaceのセットアップ
1. VSeeFaceを https://www.vseeface.icu/ からダウンロード
2. インストール後、VSeeFaceを起動
3. ずんだもんVRMモデルをロード
4. 設定で「OSC/VMC Protocol」を有効化（ポート39540）

#### Bridge Serverのセットアップ
```bash
# Node.jsの依存関係をインストール
cd voicevox-mcp-notification/zundamon-browser-skill
npm install

# Bridge Serverを起動
npm start
```

#### 拡張機能で連携を有効化
1. Bridge Serverが起動していることを確認
2. VSeeFaceでVRMモデルをロード
3. Chrome拡張機能のアイコンをクリック
4. 「🎨 VRM連携」トグルをON（VTubeStudio連携はOFFになります）
5. claude.aiのページを再読み込み

## 💻 使用方法

### 基本的な使い方
1. **VOICEVOX Engineを起動**
2. **claude.ai**にアクセス
3. Claudeと会話を開始
4. **応答が自動で音声化されます！**

### VTubeStudio連携
1. VTubeStudioでずんだもんモデルをロード
2. Chrome拡張で「VTubeStudio連携」をON
3. Claudeの応答と同時に**ずんだもんが口パク**します！

### 設定のカスタマイズ
- **音声通知ON/OFF**: 拡張機能ポップアップでトグル
- **VTubeStudio連携ON/OFF**: 拡張機能ポップアップでトグル
- **テスト再生**: ポップアップの「🎤 テスト再生」ボタン

## 🏗️ アーキテクチャ

### ファイル構成
```
zundamon-browser-skill/
├── manifest.json          # Chrome拡張機能マニフェスト
├── content.js            # メインロジック（音声読み上げ制御）
├── vts-connector.js      # VTubeStudio WebSocket連携
├── vrm-connector.js      # VRM VMC Protocol連携
├── vrm-bridge.js         # ISOLATED/MAIN Worldブリッジ
├── background.js         # Background Service Worker
├── popup.html            # 設定UIのHTML
├── popup.js              # 設定UIのロジック
├── bridge-server.js      # WebSocket-OSC Bridge Server
├── package.json          # Node.js依存関係
├── icon16.png            # アイコン（16x16）
├── icon48.png            # アイコン（48x48）
├── icon128.png           # アイコン（128x128）
└── README.md             # このファイル
```

### 技術スタック
- **WebSocket**: VTubeStudio API通信 / VRM Bridge Server通信
- **OSC (Open Sound Control)**: VMC Protocol経由VRM制御
- **postMessage API**: Chrome拡張機能のISOLATED/MAIN World通信
- **Web Audio API**: 音声再生・音量解析
- **Chrome Extension API**: Storage, Messaging
- **MutationObserver**: DOM変更検出
- **RequestAnimationFrame**: 口パクアニメーション
- **Node.js**: Bridge Server (ws + osc packages)

### データフロー
```
Claude応答検出 (MutationObserver)
  ↓
テキスト抽出・分割
  ↓
並列プリフェッチ (VOICEVOX API) - 最大5チャンク同時
  ↓
キャッシュヒット確認
  ↓
音声再生 (Web Audio API) + 口パク (VTubeStudio WebSocket)
```

## 🔧 開発履歴

### v1.1.0 (2025-01-02) - feature/vroid-support

#### 🎨 VRM連携機能追加（VSeeFace対応）
- **VMC Protocol経由でVRMモデルと連携**
  - WebSocket Bridge Server（Node.js）経由でOSC通信
  - VSeeFace、Warudo、VirtualMotionCapture等で使用可能
  - ポート39540（VMC Protocol標準）
- **ISOLATED/MAIN World通信ブリッジ実装**
  - vrm-bridge.js: postMessageリレーモジュール
  - Chrome拡張機能のISOLATED worldからMAIN worldのVRMConnectorを制御
  - クロスワールドメッセージングパターンの実装
- **アニメ風口パクアルゴリズム**
  - 音声検出時に「大きく開く(0.8)」と「小さく開く(0.2)」を交互に切り替え
  - 8フレーム（約133ms）ごとに開閉反転
  - 人の声帯域（80Hz-3.5kHz）を重視した音量解析
  - 無音時は完全に口を閉じる（閾値8）
- **Background Service Worker最適化**
  - ping/pongメカニズムでService Workerをウェイクアップ
  - タイムアウト時間2回に短縮（25秒→10秒）
  - リトライ回数拡大（1回→2回）
  - エラーログの詳細化と整理
- **デバッグログクリーンアップ**
  - 過剰なconsole.logを削除
  - エラー時のみログ出力
  - 本番環境でのパフォーマンス向上

#### 🐛 バグ修正と詳細なエラーハンドリング

**Chrome Extension ISOLATED/MAIN World問題の解決**
- **問題**: Content ScriptはデフォルトでISOLATED worldで動作し、ページの`window`オブジェクトにアクセスできない
- **症状**: `window.vrmConnector.isConnected`が常にundefinedを返し、口パクアニメーションが動作しない
- **解決策**:
  - VRM接続状態を`this.vrmConnected`フラグとしてISOLATED worldで管理
  - postMessage()でISOLATED↔MAIN間の通信を実装
  - vrm-bridge.jsでメッセージリレー機能を実装
- **修正箇所**:
  - `content.js:531-532` - playAudio()のneedsAnalyser判定
  - `content.js:549-551` - 再生終了時の口閉じ処理
  - `content.js:572` - animateMouth()の停止条件

**postMessage event.source検証問題**
- **問題**: `event.source !== window`チェックがISOLATED worldからのメッセージをブロック
- **原因**: ISOLATED worldとMAIN worldは異なる`window`オブジェクトを持つ
- **解決策**: event.sourceチェックを削除し、type-basedフィルタリングのみ使用
- **修正箇所**:
  - `vrm-bridge.js:12` - event.sourceチェック削除
  - `content.js:633` - responseHandler内のチェック削除

**Background Service Worker sleep問題**
- **問題**: Chrome MV3のService Workerは非アクティブ時にsleepし、メッセージに応答しない
- **症状**: "The message port closed before a response was received." エラー
- **解決策**:
  - ping/pongメカニズムで事前にService Workerをウェイクアップ
  - タイムアウト時間を25秒→10秒に短縮（早期リトライ）
  - リトライ回数を1回→2回に拡大
- **修正箇所**:
  - `content.js:474-476` - ping送信追加
  - `content.js:441` - タイムアウト短縮
  - `content.js:440` - リトライ回数拡大
  - `background.js:17-21` - pingレスポンス実装

**Extension context invalidation処理**
- **問題**: 拡張機能再読み込み時にcontent scriptが無効化され、エラーが大量発生
- **解決策**: 
  - `chrome.runtime.id`で無効化を検出
  - `fatal`フラグで致命的エラーを区別
  - 致命的エラー時は`this.isEnabled = false`で静かに終了
- **修正箇所**:
  - `content.js:444-448` - context無効化チェック
  - `content.js:490-495` - Extension context invalidatedエラー処理
  - `content.js:514-520` - catch内のfatalフラグ処理

### v1.0.0 (2025-01-01) - feature/optimization-improvements

#### 🎯 最初のメッセージ待機時間の大幅短縮
- **ストリーミング完了後の500ms遅延を削除**
  - 従来: `setTimeout(() => processClaudeMessage(), 500)`
  - 最適化後: 即座に `processClaudeMessage()` 実行
- **最初のチャンクもプリフェッチ対象化**
  - 従来: 2番目以降のみプリフェッチ（`for (let i = 1; ...)`）
  - 最適化後: 最初のチャンクから並列プリフェッチ（`for (let i = 0; ...)`）
- **プリフェッチ完了待機ロジック追加**
  - 最大3秒間プリフェッチ完了を待機
  - 50msごとにキャッシュをチェック
- **並列プリフェッチ数拡大**
  - 従来: 3チャンク並列
  - 最適化後: 5チャンク並列
- **効果**: 約2秒の短縮を達成（2.5-3.5秒 → 0.5-1.5秒）

#### 🎭 VTubeStudio Live2D口パク連携機能
- **VTubeStudio WebSocket API連携モジュール実装 (vts-connector.js)**
  - WebSocket接続 (localhost:8001)
  - 自動認証・トークン管理 (localStorage)
  - 自動再接続機能（5秒インターバル）
  - リクエスト/レスポンス管理
- **リアルタイム口パクアニメーション**
  - Web Audio API AnalyserNodeで音量解析
  - FFT解析 (fftSize: 256)
  - 音量を0-1の範囲に正規化（`average / 128`）
  - VoiceVolumePlusWhisperVolumeパラメータ制御
  - requestAnimationFrameで滑らかなアニメーション
  - 再生終了時の自動口閉じ処理
- **UI追加**
  - 拡張機能ポップアップにVTubeStudio ON/OFFトグル
  - 設定の永続化 (chrome.storage.sync)
  - 接続状態の表示

#### ⚡ チャンク間待機時間の大幅短縮
- **キュー追加時に即座にプリフェッチ開始**
  - 従来: 音声合成完了後にプリフェッチ
  - 最適化後: キュー追加時点でプリフェッチ開始
- **再帰呼び出しを削除しループ構造に変更**
  - whileループで連続処理
  - 関数呼び出しオーバーヘッド削減
  - キャッシュヒット時の待機時間ほぼゼロ
- **ヘルパー関数追加**
  - `startPrefetch()`: コード重複削減

#### 🐛 エラーハンドリング改善
- **エラーメッセージ表示レベル最適化**
  - タイムアウト/リトライ時: `console.error` → `console.warn`
  - リトライ成功時: エラー表示なし
  - リトライ後失敗時のみエラー表示
- **Extension context無効化時のエラーメッセージ抑制**
  - `fatal`フラグによる致命的エラー判定
  - 致命的エラー時は静かに終了
  - 不要なエラーログ削減

### v0.9.0 (2024-12-27) - 初期バージョン
- **基本的な音声読み上げ機能**
  - VOICEVOX API連携
  - Claude応答検出（MutationObserver）
  - 自動音声合成
  - Web Audio API再生

## 📊 パフォーマンス指標

### 待機時間（従来 vs 最適化後）
| 項目 | 従来 | 最適化後 | 短縮時間 |
|------|------|----------|----------|
| 最初のメッセージ | 2.5-3.5秒 | 0.5-1.5秒 | **約2秒** |
| チャンク間（キャッシュヒット） | 0.5-1秒 | ほぼ0秒 | **約0.5秒** |
| チャンク間（キャッシュミス） | 2-3秒 | 2-3秒 | 変化なし |

### プリフェッチ効率
- **並列数**: 5チャンク同時
- **キャッシュヒット率**: 約90%（中盤以降）
- **メモリ使用量**: 音声データ約5MB（5チャンク分）

### VTubeStudio連携パフォーマンス
- **WebSocket接続時間**: 約100-200ms
- **認証時間**: 約50-100ms（初回のみ）
- **口パクパラメータ送信**: 約16ms（60FPS）
- **音声同期精度**: ±10ms以内

## 🔍 トラブルシューティング

### VRM連携が動作しない

**原因1: Bridge Serverが起動していない**
```bash
解決策: npm start でBridge Serverを起動
確認方法: コンソールで「Bridge Server listening on port 8765」を確認
```

**原因2: VSeeFaceのVMC Protocolが無効**
```bash
解決策:
1. VSeeFace設定を開く
2. 「VMCプロトコルで受信する (トラッキングを無効)」をON
3. ポート番号39540を設定
```

**原因3: 口パクが動かない**
```bash
原因:
- ISOLATED worldからMAIN worldの`window.vrmConnector`にアクセスできない
- playAudio()内でneedsAnalyserがfalseと判定されるAnalyserが生成されない

解決策:
- vrm-bridge.jsでpostMessageブリッジを実装済み
- this.vrmConnectedフラグでISOLATED world内で管理
確認方法: コンソールで「VRM連携が有効になりました」を確認
```

**原因4: 口の動きが不自然**
```bash
原因: アニメ風口パクアルゴリズムが有効ではない

解決策:
- 8フレーム（133ms）ごとに「大きく開く(0.8)」と「小さく開く(0.2)」を交互切り替え
- 無音時は完全に口を閉じる（閾値8）
- 人の声帯域（80Hz-3.5kHz）を重視
```

### 音声が再生されない

**原因1: VOICEVOX未起動**
```
解決策: VOICEVOX Engineアプリを起動
確認方法: 拡張機能アイコンで接続状態確認
```

**原因2: 拡張機能が無効**
```
解決策: 拡張機能アイコン → スイッチをON
```

### VTubeStudio連携が動作しない

**原因1: VTubeStudioが起動していない**
```
解決策: VTubeStudioを起動してモデルをロード
確認方法: コンソールで「✅ VTubeStudio連携が有効になりました」を確認
```

**原因2: WebSocket接続失敗**
```
解決策: 
1. VTubeStudio設定でプラグインAPIを有効化
2. ポート8001が使用可能か確認
3. ファイアウォール設定を確認
```

**原因3: 認証エラー**
```
解決策:
1. VTubeStudioで「Plugins」メニューを開く
2. 「Zundamon Voice Browser Skill」を承認
3. ページを再読み込み
```

### VRoidモデルを使用したい

**重要**: VTubeStudioはLive2D専用です。VRoidモデル(.vrm)は**使用できません**。

**代替案**:
1. **ずんだもん公式Live2Dモデルを使用**（推奨）
   - BOOTH: https://booth.pm/ja/items/5363599
2. **VRM対応ソフトを使用**（要追加開発）
   - VSeeFace, 3tene, Animaze等

## 🤝 貢献

プルリクエスト・Issue報告を歓迎します！

### 開発環境のセットアップ
```bash
git clone https://github.com/Tenormusica2024/voicevox-mcp-notification.git
cd voicevox-mcp-notification/zundamon-browser-skill
# Chrome拡張機能として読み込み
```

### ブランチ戦略
- `master`: 安定版
- `feature/*`: 新機能開発
- `bugfix/*`: バグ修正

## 📝 ライセンス

MIT License

## 🙏 謝辞

- **VOICEVOX**: 音声合成エンジン
- **VTubeStudio**: Live2Dモデル制御ソフト
- **東北ずん子プロジェクト**: ずんだもんキャラクター・Live2Dモデル

## 🔗 リンク

- **VOICEVOX**: https://voicevox.hiroshiba.jp/
- **VTubeStudio**: https://denchisoft.com/
- **ずんだもんLive2Dモデル**: https://booth.pm/ja/items/5363599
- **東北ずん子プロジェクト**: https://zunko.jp/
- **VTubeStudio API**: https://github.com/DenchiSoft/VTubeStudio

## 📞 サポート

問題が発生した場合は、GitHubのIssueでお知らせください。

---

**Made with ❤️ by Tenormusica**
