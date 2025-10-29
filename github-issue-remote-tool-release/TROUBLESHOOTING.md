# トラブルシューティングガイド

## 🚨 セットアップ時のエラー

### エラー: `config.jsonが見つかりません`

**原因**: セットアップウィザードを実行していない

**解決方法**:
```cmd
python setup_wizard.py
```

### エラー: `認証失敗: 401`

**原因**: GitHub Personal Access Tokenが無効または期限切れ

**解決方法**:
1. https://github.com/settings/tokens にアクセス
2. 既存のトークンが有効か確認
3. 無効な場合は新しいトークンを生成
4. `setup_wizard.py` を再実行して新しいトークンを設定

### エラー: `リポジトリが見つかりません: 404`

**原因**: 
- リポジトリ名が間違っている
- トークンに適切なスコープがない
- プライベートリポジトリなのに `public_repo` スコープしかない

**解決方法**:
1. リポジトリ名を確認（`owner/repository`形式）
2. トークンのスコープを確認
3. プライベートリポジトリの場合は `repo` スコープが必要

### エラー: `Issue #X が見つかりません: 404`

**原因**: Issue番号が間違っている、またはIssueが存在しない

**解決方法**:
1. GitHubでIssue番号を確認
2. Issueが削除されていないか確認
3. 正しいIssue番号で `setup_wizard.py` を再実行

### 座標検出に失敗する

**原因**: Claude Codeウィンドウが見つからない

**解決方法**:
1. Claude Codeを起動
2. Claude Codeウィンドウをアクティブ（前面）にする
3. セットアップウィザードで座標を手動設定:
   - 「座標を手動調整しますか？」で `y` を入力
   - Claude Code上部入力欄の座標を入力
   - Claude Code下部入力欄の座標を入力

**座標の確認方法**:
1. Claude Codeを起動
2. マウスカーソルを入力欄の中央に移動
3. Python で座標確認:
   ```python
   import pyautogui
   pyautogui.position()  # 現在のマウス座標を表示
   ```

## 🔧 監視サービスのエラー

### エラー: `初期化エラー: config.jsonが見つかりません`

**原因**: 監視サービスを起動したフォルダに `config.json` がない

**解決方法**:
1. 正しいフォルダに移動
2. `ls` または `dir` で `config.json` の存在を確認
3. 存在しない場合は `setup_wizard.py` を実行

### エラー: `GitHub API接続エラー`

**原因**: インターネット接続の問題、またはGitHub APIの制限

**解決方法**:
1. インターネット接続を確認
2. `https://www.githubstatus.com/` でGitHubのステータスを確認
3. ファイアウォール設定を確認
4. プロキシ環境の場合はプロキシ設定を確認

### エラー: `Claude Code貼り付けエラー`

**原因**: 
- Claude Codeが起動していない
- 座標設定が間違っている
- Claude Codeウィンドウの位置が変わった

**解決方法**:
1. Claude Codeを起動
2. `config.json` の座標を確認:
   ```json
   "claude_code_coords": {
     "upper": [1357, 539],
     "lower": [1357, 1056]
   }
   ```
3. 座標が正しくない場合は `setup_wizard.py` を再実行

### コメントが転送されない

**チェックリスト**:
- [ ] `monitor_service.py` が起動していますか？
- [ ] コマンド形式は正しいですか？（`upper:` または `lower:` で始まる）
- [ ] コメントがシステムコメントではないですか？（`📸` や `**Screenshot**` を含む）
- [ ] `monitor_service.log` にエラーが記録されていませんか？

**ログ確認**:
```cmd
type monitor_service.log
```

最新50行を確認:
```cmd
powershell "Get-Content monitor_service.log -Tail 50"
```

### スクリーンショットがアップロードされない

**原因**:
- トークンに書き込み権限がない
- ブランチが保護されている
- ネットワークエラー

**解決方法**:
1. トークンのスコープを確認（`repo` が必要）
2. リポジトリの設定でブランチ保護を確認
3. `monitor_service.log` でエラー詳細を確認

## 🐛 動作がおかしい場合

### 座標がずれている

**原因**: 
- ディスプレイ解像度が変わった
- Claude Codeウィンドウのサイズが変わった
- マルチディスプレイ環境で配置が変わった

**解決方法**:
```cmd
python setup_wizard.py
```
ステップ3の座標検出を再実行

### 重複してコメントが処理される

**原因**: 複数の `monitor_service.py` が起動している

**解決方法**:
1. タスクマネージャーでPythonプロセスを確認
2. 重複しているプロセスを終了
3. `monitor_service.py` を1つだけ起動

### Claude Codeが応答しない

**チェックリスト**:
- [ ] Claude Codeが起動していますか？
- [ ] Claude Codeウィンドウがフリーズしていませんか？
- [ ] 座標設定が正しいですか？
- [ ] キーボード入力が効きますか？（手動でテスト）

**デバッグ手順**:
1. Claude Codeを再起動
2. 手動で入力欄をクリックしてテキスト入力
3. 入力できない場合はClaude Codeの問題
4. 入力できる場合は座標設定の問題 → `setup_wizard.py` 再実行

## 📊 ログの読み方

### 正常な動作ログ

```
[2025-01-19 10:00:00] INFO - Issue監視サービス開始
[2025-01-19 10:00:00] INFO - Repository: username/repository Issue #1
[2025-01-19 10:00:00] INFO - Poll interval: 5秒
[2025-01-19 10:00:05] INFO - 全1ページから合計5個のコメントを取得
[2025-01-19 10:00:10] INFO - 転送開始（下部ペイン）: コメント#12345 by @username
[2025-01-19 10:00:10] INFO -   [SUCCESS] 転送成功: Claude Code下部ペインに送信完了
```

### エラーログの例

```
[2025-01-19 10:00:00] ERROR - GitHub API接続エラー: HTTPSConnectionPool(host='api.github.com', port=443)
```
→ インターネット接続を確認

```
[2025-01-19 10:00:00] ERROR - Claude Code貼り付けエラー: pyautogui.FailSafeException
```
→ マウスカーソルが画面の角に移動した（PyAutoGUIの安全機能）

```
[2025-01-19 10:00:00] ERROR - スクリーンショットアップロード失敗: 403 Forbidden
```
→ トークンの権限不足

## 🔍 詳細デバッグ

### ログレベルを上げる

`monitor_service.py` の22行目を編集:
```python
level=logging.DEBUG,  # INFOからDEBUGに変更
```

これにより、より詳細なログが記録されます。

### ネットワーク接続テスト

```python
import requests
headers = {"Authorization": "Bearer YOUR_TOKEN"}
r = requests.get("https://api.github.com/user", headers=headers)
print(r.status_code, r.json())
```

### 座標テスト

```python
import pyautogui
import time

# 5秒後に現在のマウス位置を表示
time.sleep(5)
print(pyautogui.position())

# クリックテスト（Claude Code入力欄にカーソルを移動してから実行）
time.sleep(5)
pyautogui.click()
```

## 💡 パフォーマンス改善

### ポーリング間隔の調整

`config.json` の `poll_interval` を変更:
```json
{
  "poll_interval": 10  // 5秒 → 10秒に変更（負荷軽減）
}
```

### ログファイルのローテーション

ログファイルが大きくなりすぎた場合:
```cmd
del monitor_service.log
```
監視サービスを再起動すると新しいログファイルが作成されます。

## 📞 サポート依頼時の情報

以下の情報を添えてサポートに連絡してください:

1. **エラーメッセージ**（スクリーンショット）
2. **ログファイル**（最新50-100行）:
   ```cmd
   powershell "Get-Content monitor_service.log -Tail 100" > debug_log.txt
   ```
3. **環境情報**:
   ```cmd
   python --version
   pip list
   systeminfo | findstr /B /C:"OS Name" /C:"OS Version"
   ```
4. **config.json**（トークン部分は `***` に置き換え）
5. **再現手順**（何をしたらエラーが発生したか）

---

**問題が解決しない場合**: README.mdの「サポート」セクションを参照してください。