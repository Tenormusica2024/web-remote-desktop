# 🔊 ずんだもん音声通知システム - MCP直接呼び出し版

## 📋 概要

VOICEVOX APIを直接呼び出してClaude Codeの作業フローに音声通知を統合するシステムです。

**改修内容:**
- ❌ **旧実装**: GitHub Issue経由の間接的な通知（レイテンシー大）
- ✅ **新実装**: VOICEVOX API直接呼び出し（リアルタイム通知）

---

## 🎯 主な機能

### 1. 直接MCP呼び出し
- VOICEVOX APIに直接HTTPリクエストを送信
- レイテンシー削減（Issue投稿→ポーリング→実行の遅延を解消）
- リアルタイム音声通知が可能

### 2. フォールバック機構
- VOICEVOX API接続失敗時は自動的にGitHub Issue経由にフォールバック
- 通知の確実性を保証

### 3. 豊富な通知メソッド
```python
notifier = ClaudeVoiceNotifier()

# タスク開始
notifier.notify_task_start("プロジェクト名")

# デプロイ開始
notifier.notify_deploy_start("sound-platform")

# デプロイ完了
notifier.notify_deploy_complete("sound-platform")

# エラー発生
notifier.notify_error("デプロイ失敗")

# タスク完了
notifier.notify_task_complete("UI修正とデプロイ")

# Git push完了
notifier.notify_git_push("feature-branch")

# ファイル編集完了
notifier.notify_file_edit("app.py")

# 質問通知（Claude → ユーザー）
notifier.notify_question("どちらのサービスにデプロイしますか?")

# 回答通知（ユーザーの質問への回答）
notifier.notify_answer("現在のリビジョンは100です")

# 一般応答通知（確認・報告など）
notifier.notify_response("承知しました。実装を開始します")

# カスタム通知
notifier.notify("カスタムメッセージ", "progress")
```

---

## 🚀 セットアップ

### 前提条件
1. **VOICEVOX Engine起動**
   - VOICEVOX Engineが `http://localhost:50021` で起動していること
   - ずんだもん音声（Speaker ID: 3）が利用可能なこと

2. **Python環境**
   - Python 3.7以上
   - 標準ライブラリのみ使用（追加インストール不要）

### 動作確認

```bash
# テストスクリプト実行
cd C:\Users\Tenormusica\Documents\github-remote-desktop
python test_voice_notification.py
```

**期待される動作:**
1. 「テストメッセージです」の音声が再生される
2. 「ずんだもんプロジェクト改修を開始します」の音声が再生される
3. 「音声通知実装が完了しました」の音声が再生される
4. 「テストエラーが発生しました」の音声が再生される

---

## 🔧 使用方法

### コマンドラインから実行

```bash
# タスク開始通知
python claude_voice_notification.py task_start "記事作成"

# デプロイ開始通知
python claude_voice_notification.py deploy_start "sound-platform"

# デプロイ完了通知
python claude_voice_notification.py deploy_complete "sound-platform"

# エラー通知
python claude_voice_notification.py error "デプロイ失敗"

# タスク完了通知
python claude_voice_notification.py task_complete "UI修正とデプロイ"

# Git push完了通知
python claude_voice_notification.py git_push "feature-branch"

# ファイル編集完了通知
python claude_voice_notification.py file_edit "app.py"

# 質問通知
python claude_voice_notification.py question "どちらのサービスにデプロイしますか?"

# 回答通知
python claude_voice_notification.py answer "現在のリビジョンは100です"

# 一般応答通知
python claude_voice_notification.py response "承知しました。実装を開始します"

# カスタム通知
python claude_voice_notification.py custom "Git pushが完了しました" "complete"
```

### Python スクリプトから実行

```python
from claude_voice_notification import ClaudeVoiceNotifier

notifier = ClaudeVoiceNotifier()

# 任意のタイミングで音声通知
notifier.notify("記事公開が完了しました", "complete")
```

---

## 🏗️ アーキテクチャ

### 通知フロー

```
1. Python Script
   ↓
2. ClaudeVoiceNotifier.notify()
   ↓
3. _synthesize_and_play()
   ↓
4. VOICEVOX API (localhost:50021)
   ├─ POST /audio_query → 音声クエリ生成
   ├─ POST /synthesis → WAVファイル生成
   └─ PowerShell → 音声再生
   ↓
5. 成功 or フォールバック
   ↓
6. （フォールバック時）GitHub Issue投稿
```

### エラーハンドリング

```python
try:
    # VOICEVOX API直接呼び出し
    success = _synthesize_and_play(message)
    if success:
        return True
except Exception as e:
    # 失敗時は自動的にフォールバック
    return _fallback_issue_notification(message, status)
```

---

## 🔍 トラブルシューティング

### 音声が再生されない

**原因1: VOICEVOX Engineが起動していない**
```bash
# VOICEVOX Engine起動確認
curl http://localhost:50021/version
```

**解決策:**
- VOICEVOX Engineアプリケーションを起動する

**原因2: ポート50021が使用中**
```bash
# ポート使用状況確認
netstat -ano | findstr :50021
```

**解決策:**
- `claude_voice_notification.py` の `self.voicevox_api` を変更

**原因3: Speaker ID不一致**
```python
# claude_voice_notification.py で変更
self.speaker_id = 3  # ずんだもん ノーマル
# 他のキャラクター:
# 1: 四国めたん
# 8: 春日部つむぎ
# 10: 雨晴はう
```

### フォールバック通知が届かない

**原因: GitHub認証情報の問題**
```bash
# task_complete_private.py の動作確認
cd C:\Users\Tenormusica\Documents\github-remote-desktop
python task_complete_private.py "テスト通知"
```

---

## 📊 実装詳細

### VOICEVOX API仕様

**エンドポイント:**
- `POST /audio_query?text={text}&speaker={speaker_id}`
  - 音声クエリ生成
  - 返り値: JSON（音声パラメータ）

- `POST /synthesis?speaker={speaker_id}`
  - 音声合成
  - リクエストボディ: 音声クエリJSON
  - 返り値: WAV形式バイナリ

**Speaker ID:**
- 3: ずんだもん ノーマル（デフォルト）
- 詳細: http://localhost:50021/speakers

### Windows音声再生

```powershell
# PowerShell SoundPlayer使用
(New-Object System.Media.SoundPlayer '{wav_file_path}').PlaySync()
```

**特徴:**
- 追加ソフトウェア不要
- 同期再生（再生完了まで待機）
- WAV形式のみ対応

---

## 🎯 使用シーン別ガイド

### 1. タスク完了報告
```bash
# 具体的な作業内容を読み上げ
python claude_voice_notification.py task_complete "UI修正とデプロイ"
python claude_voice_notification.py task_complete "記事執筆とZenn投稿"
python claude_voice_notification.py task_complete "バグ修正とテスト実行"
```

### 2. 会話・質疑応答
```bash
# Claude → ユーザーへの質問
python claude_voice_notification.py question "どちらのサービスにデプロイしますか?"
python claude_voice_notification.py question "現在のリビジョン番号を教えてください"

# ユーザーの質問への回答
python claude_voice_notification.py answer "現在のリビジョンは100です"
python claude_voice_notification.py answer "画面左上のブラウザで再生されているのはリーグオブレジェンドです"

# 一般的な応答・確認
python claude_voice_notification.py response "承知しました。実装を開始します"
python claude_voice_notification.py response "スクリーンショットを撮影しました"
```

### 3. 開発作業通知
```bash
# Git操作
python claude_voice_notification.py git_push "feature-branch"
python claude_voice_notification.py git_push "main"

# ファイル編集
python claude_voice_notification.py file_edit "app.py"
python claude_voice_notification.py file_edit "README.md"

# デプロイ
python claude_voice_notification.py deploy_start "sound-platform"
python claude_voice_notification.py deploy_complete "sound-platform"
```

### 4. 長文の音声通知
長い回答を複数パートに分けて順番に読み上げることも可能：
```bash
python claude_voice_notification.py response "AIの登場で確かに書く作業は楽になりましたが、同時に基礎力の低下というジレンマも生まれています"
python claude_voice_notification.py response "懸念すべき点として、AIが生成したコードのなぜそうなるのかを理解できないと、デバッグや最適化が困難になります"
python claude_voice_notification.py response "前向きに考えられる点として、AIを使いながら学ぶという新しい学習スタイルも可能です"
```

## 🎯 今後の拡張案

### フェーズ4: Claude Code Hook統合
```json
// .claude-hooks.json
{
  "afterToolUse": {
    "task_complete_private": {
      "command": "python",
      "args": [
        "C:/Users/Tenormusica/Documents/github-remote-desktop/claude_voice_notification.py",
        "task_complete",
        "タスク"
      ]
    }
  }
}
```

### フェーズ5: 使用統計ログ
- 通知履歴のJSON記録
- 使用頻度・エラー率の可視化
- 改善のためのデータ収集

---

## 📝 変更履歴

### v3.0.0 (2025-10-28)
- ✅ **会話型通知機能を追加**
  - `notify_question()`: Claude → ユーザーへの質問を読み上げ
  - `notify_answer()`: ユーザーの質問への回答を読み上げ
  - `notify_response()`: 一般的な応答・確認・報告を読み上げ
- ✅ **具体的メッセージ読み上げ機能を実装**
  - 固定メッセージ（「タスクが完了しました」）から具体的メッセージ（「UI修正とデプロイが完了しました」）へ変更
  - `notify_git_push()`: Git pushのブランチ名を読み上げ
  - `notify_file_edit()`: 編集したファイル名を読み上げ
- ✅ **音声カスタマイズ機能を廃止**
  - 複数キャラクター・複数スタイルの実装を削除
  - ずんだもんノーマル音声に統一してシンプル化

### v2.0.0 (2025-10-27)
- ✅ VOICEVOX API直接呼び出しに変更
- ✅ フォールバック機構の実装
- ✅ リアルタイム音声通知を実現
- ✅ レイテンシー削減（Issue経由を廃止）

### v1.0.0 (以前)
- GitHub Issue経由の間接的な通知
- レイテンシー大（ポーリング依存）

---

## 🔗 関連ファイル

- `claude_voice_notification.py` - メイン実装
- `test_voice_notification.py` - テストスクリプト
- `task_complete_private.py` - フォールバック用Issue投稿
- `.claude/mcp_config.json` - VOICEVOX MCP設定
- `.claude/hooks/zundamon-voice-notification.js` - Hook実装（旧）

---

## 📞 サポート

問題が発生した場合:
1. VOICEVOX Engineの起動を確認
2. `test_voice_notification.py` で動作確認
3. ログファイル確認: `%TEMP%\zundamon-hook.log`
