# ずんだもん音声拡張機能の今後の機能拡張案

## 📋 概要

Claude Web版ずんだもん音声拡張機能の今後の機能拡張・改善案をリストアップします。

---

## 🎯 優先度: 高

### 1. 音声速度調整機能

**目的:** 読み上げ速度をユーザーの好みに合わせて調整可能にする

**実装方法:**
- VOICEVOXの`speedScale`パラメータを使用
- ポップアップUIにスライダーを追加（0.5倍速～2.0倍速）
- デフォルト: 1.0倍速

**技術的詳細:**
```javascript
// audio_query取得後にspeedScaleを調整
const audioQuery = await queryResponse.json();
audioQuery.speedScale = 1.5; // ユーザー設定値
```

**期待効果:**
- レスポンス速度の体感向上
- ユーザー個別の聴きやすさに対応

---

### 2. キャラクター選択機能

**目的:** ずんだもん以外のVOICEVOXキャラクターを選択可能にする

**実装方法:**
- ポップアップUIにキャラクター選択ドロップダウンを追加
- 主要キャラクター（四国めたん、ずんだもん、春日部つむぎ等）をプリセット
- Speaker IDをChrome Storageに保存

**技術的詳細:**
```javascript
// キャラクター一覧
const characters = [
  { id: 3, name: 'ずんだもん（ノーマル）' },
  { id: 1, name: 'ずんだもん（あまあま）' },
  { id: 2, name: '四国めたん（ノーマル）' },
  { id: 8, name: '春日部つむぎ（ノーマル）' }
];
```

**期待効果:**
- ユーザーの好みに合わせたキャラクター選択
- 長時間使用時の飽き防止

---

### 3. 読み上げON/OFF切り替えショートカットキー

**目的:** キーボードショートカットで即座に読み上げを制御

**実装方法:**
- Chrome Extension Commands APIを使用
- デフォルト: `Ctrl+Shift+Z`（カスタマイズ可能）
- manifest.jsonにcommands定義を追加

**技術的詳細:**
```json
"commands": {
  "toggle-voice": {
    "suggested_key": {
      "default": "Ctrl+Shift+Z"
    },
    "description": "音声読み上げON/OFF切り替え"
  }
}
```

**期待効果:**
- 即座の制御による利便性向上
- 他の作業との並行使用時に便利

---

## 🎯 優先度: 中

### 4. 読み上げ範囲の設定

**目的:** 全文/要約/最初の文など、読み上げ範囲を選択可能にする

**実装方法:**
- ポップアップUIにラジオボタンで選択肢を追加
- 選択肢: 全文、最初の文のみ、100文字要約、カスタム文字数

**技術的詳細:**
```javascript
const modes = {
  FULL: 'full',           // 全文
  FIRST_SENTENCE: 'first', // 最初の文のみ
  SUMMARY_100: 'summary',  // 100文字要約
  CUSTOM: 'custom'         // カスタム文字数
};
```

**期待効果:**
- 長文応答時の時間短縮
- 概要のみ把握したい場合に便利

---

### 5. 頻出フレーズの事前合成キャッシュ

**目的:** よく使われるフレーズを事前に音声合成してキャッシュ、レスポンス速度向上

**実装方法:**
- IndexedDBにキャッシュストレージ作成
- 頻出フレーズ（「わかりました」「ありがとうございます」等）を起動時に合成
- テキストマッチ時はキャッシュから即座再生

**技術的詳細:**
```javascript
const commonPhrases = [
  'わかりました',
  'ありがとうございます',
  'こんにちは',
  'おはようございます',
  'こんばんは'
];

// 起動時に事前合成
await preloadCommonPhrases(commonPhrases);
```

**期待効果:**
- 短い応答時のレスポンス速度が劇的に向上
- API呼び出し削減によるVOICEVOX負荷軽減

---

### 6. 読み上げ履歴表示

**目的:** 過去に読み上げたテキストの履歴を表示・再生

**実装方法:**
- ポップアップUIに履歴タブを追加
- 最新20件程度をChrome Storageに保存
- クリックで再読み上げ可能

**技術的詳細:**
```javascript
// 履歴オブジェクト
const historyEntry = {
  text: '読み上げたテキスト',
  timestamp: Date.now(),
  audioData: [...] // キャッシュ済み音声データ
};
```

**期待効果:**
- 聞き逃した内容の確認
- 重要な応答の繰り返し再生

---

## 🎯 優先度: 低（将来的な検討）

### 7. 感情表現の自動調整

**目的:** テキスト内容から感情を推測し、VOICEVOXの感情パラメータを調整

**実装方法:**
- 感嘆符・疑問符の数をカウント
- ポジティブ/ネガティブワード検出
- intonationScale, pitchScaleを動的調整

**技術的詳細:**
```javascript
// 感情スコア計算
const exclamationCount = (text.match(/！|!/g) || []).length;
const questionCount = (text.match(/？|\?/g) || []).length;

audioQuery.intonationScale = 1.0 + (exclamationCount * 0.1);
```

**期待効果:**
- より自然な読み上げ
- 感情表現の豊かさ向上

---

### 8. 多言語対応

**目的:** 英語・中国語など他言語の応答も読み上げ可能にする

**実装方法:**
- 言語検出ライブラリを使用
- 言語別に適切なTTSエンジンを選択
- VOICEVOX以外のエンジン（Web Speech API等）も統合

**技術的詳細:**
```javascript
// 言語検出
const lang = detectLanguage(text);

if (lang === 'ja') {
  await synthesizeWithVOICEVOX(text);
} else if (lang === 'en') {
  await synthesizeWithWebSpeechAPI(text, 'en-US');
}
```

**期待効果:**
- 多言語環境での利用可能
- グローバルユーザー対応

---

### 9. 自動要約機能の強化

**目的:** LLMを使用した高度な要約で、より的確な要約を生成

**実装方法:**
- Claude APIまたはローカルLLMを使用
- 重要文のみを抽出して要約
- ユーザー設定で要約レベル調整可能

**技術的詳細:**
```javascript
// Claude APIで要約
const summary = await fetch('https://api.anthropic.com/v1/messages', {
  method: 'POST',
  body: JSON.stringify({
    model: 'claude-3-haiku-20240307',
    messages: [{
      role: 'user',
      content: `以下のテキストを50文字以内に要約:\n${text}`
    }]
  })
});
```

**期待効果:**
- 長文応答の効率的な把握
- 重要情報の取りこぼし防止

---

### 10. バックグラウンド音楽/効果音の追加

**目的:** 読み上げ時にバックグラウンド音楽や効果音を再生して雰囲気を演出

**実装方法:**
- ユーザーが任意の音楽ファイルをアップロード
- 読み上げ開始時に低音量でBGM再生
- 読み上げ完了時に効果音（チャイム等）

**技術的詳細:**
```javascript
// Web Audio APIでミキシング
const bgmSource = audioContext.createBufferSource();
bgmSource.buffer = bgmBuffer;

const gainNode = audioContext.createGain();
gainNode.gain.value = 0.2; // 低音量

bgmSource.connect(gainNode).connect(audioContext.destination);
```

**期待効果:**
- 楽しい使用体験
- 長時間使用時の疲労軽減

---

## 🛠️ 技術的改善（内部最適化）

### 11. ストリーミング完了待機時間の最適化

**目的:** 500ms待機を動的に調整し、より早いレスポンス

**実装方法:**
- DOM更新頻度を監視
- 一定時間更新がない場合は即座処理
- 最小待機時間を100ms程度に短縮可能

**期待効果:**
- レスポンス速度向上
- 体感速度の改善

---

### 12. テキスト抽出処理の最適化

**目的:** 正規表現マッチングの高速化

**実装方法:**
- 頻繁に使用するパターンをコンパイル済みRegExpオブジェクトとして保持
- 不要なパターンマッチを削減

**期待効果:**
- CPU使用率削減
- バッテリー消費軽減

---

### 13. エラーハンドリングの強化

**目的:** VOICEVOX未起動時の適切なユーザー通知

**実装方法:**
- 初回失敗時にポップアップで通知
- VOICEVOX起動手順へのリンク表示
- 自動リトライ機能

**期待効果:**
- ユーザビリティ向上
- 初心者ユーザーの困惑防止

---

## 📝 実装優先度の判断基準

1. **ユーザー要望の多さ**
2. **実装の容易さ**
3. **パフォーマンスへの影響**
4. **既存機能との整合性**

---

## 🚀 次のステップ

各機能について：
- Issue化して詳細設計を議論
- プルリクエストでの段階的実装
- ユーザーフィードバックの収集

---

**作成日:** 2025-10-28
