# 監視スクリプト自動再起動システム

GitHub Issue監視スクリプトが停止した際に自動的に再起動するシステムです。

## 🎯 2つの方式

### 方式1: Watchdog Monitor（プロセス監視型）

定期的にプロセス存在を確認し、停止していたら再起動します。

**特徴:**
- 外部から定期的にプロセスチェック
- Windowsタスクスケジューラで5分間隔実行推奨
- 軽量・シンプル
- 複数の監視スクリプトを同時管理可能

**使用方法:**

1. **手動実行テスト:**
```cmd
python watchdog_monitor_service.py
```

2. **Windowsタスクスケジューラ設定（推奨）:**

```cmd
# タスク作成
schtasks /create /tn "GitHubIssueWatchdog" /tr "python C:\Users\Tenormusica\Documents\github-remote-desktop\watchdog_monitor_service.py" /sc minute /mo 5 /ru %USERNAME%

# タスク確認
schtasks /query /tn "GitHubIssueWatchdog"

# タスク削除（必要時）
schtasks /delete /tn "GitHubIssueWatchdog" /f
```

**設定ファイル:**

`watchdog_monitor_service.py` 内の `MONITOR_SCRIPTS` を編集：

```python
MONITOR_SCRIPTS = [
    {
        "name": "Private Issue Monitor",
        "script": "private_issue_monitor_service.py",
        "cwd": Path(__file__).parent,
        "enabled": True  # 監視有効化
    },
    {
        "name": "Multi Issue Monitor (v2)",
        "script": "github-issue-remote-tool-v2/monitor_service_multi.py",
        "cwd": Path(__file__).parent,
        "enabled": False  # 配布版使用時はTrueに変更
    }
]
```

**ログ確認:**
```cmd
type watchdog_monitor.log
```

---

### 方式2: Self-Healing Monitor（自己回復型）

監視スクリプトをラップし、クラッシュ時に自動再起動します。

**特徴:**
- プロセス内部で異常検知
- クラッシュ即座に再起動
- 短時間連続クラッシュ時は待機時間延長
- 最大再起動回数制限あり

**使用方法:**

```cmd
# Private Issue Monitor（座標ベース版）を自己回復モードで起動
python self_healing_monitor.py private_issue_monitor_service.py

# Multi Issue Monitor（配布版v2）を自己回復モードで起動
python self_healing_monitor.py github-issue-remote-tool-v2/monitor_service_multi.py
```

**バックグラウンド実行（Windowsタスクスケジューラ）:**

```cmd
# 自己回復型監視をタスクとして登録
schtasks /create /tn "SelfHealingIssueMonitor" /tr "python C:\Users\Tenormusica\Documents\github-remote-desktop\self_healing_monitor.py private_issue_monitor_service.py" /sc onstart /ru %USERNAME% /rl HIGHEST

# タスク確認
schtasks /query /tn "SelfHealingIssueMonitor"

# タスク削除（必要時）
schtasks /delete /tn "SelfHealingIssueMonitor" /f
```

**ログ確認:**
```cmd
type self_healing_monitor.log
```

---

## 📊 どちらを使うべき？

### Watchdog Monitor（推奨）

✅ **こんな場合に推奨:**
- 複数の監視スクリプトを管理したい
- 定期チェックで十分（5分間隔）
- シンプルな構成が好み
- 外部からの監視を希望

❌ **不向きな場合:**
- 即座の再起動が必要（5分待機が長い）
- プロセスが頻繁にクラッシュする

### Self-Healing Monitor

✅ **こんな場合に推奨:**
- クラッシュ即座に再起動したい
- 1つの監視スクリプトに集中
- プロセス内部の異常検知が必要
- より高度な自己回復機能を希望

❌ **不向きな場合:**
- 複数の監視スクリプトを同時管理したい
- シンプルな構成が好み

---

## 🔄 併用も可能

両方を同時に使用することも可能です：

1. **Watchdog Monitor**: Windowsタスクスケジューラで5分間隔実行
2. **Self-Healing Monitor**: 監視スクリプトをラップして起動

この場合、Self-Healing Monitorが内部でクラッシュを検知・再起動し、
万が一Self-Healing Monitor自体が停止した場合はWatchdog Monitorが検出・再起動します。

**設定例:**

```cmd
# Step 1: Watchdog Monitorをタスクスケジューラに登録（5分間隔）
schtasks /create /tn "GitHubIssueWatchdog" /tr "python C:\Users\Tenormusica\Documents\github-remote-desktop\watchdog_monitor_service.py" /sc minute /mo 5 /ru %USERNAME%

# Step 2: Self-Healing Monitor経由で監視スクリプト起動
python self_healing_monitor.py private_issue_monitor_service.py
```

---

## 🛠 トラブルシューティング

### Watchdog Monitorが再起動しない

**確認項目:**
1. `watchdog_monitor.log` で詳細確認
2. `MONITOR_SCRIPTS` で `enabled: True` になっているか
3. スクリプトパスが正しいか
4. Pythonプロセスとして実行されているか

### Self-Healing Monitorが動作しない

**確認項目:**
1. `self_healing_monitor.log` で詳細確認
2. スクリプトパスが正しいか（相対パスまたは絶対パス）
3. 最大再起動回数に到達していないか
4. 監視対象スクリプトが存在するか

### タスクスケジューラが実行されない

**確認項目:**
1. タスクスケジューラで「最新の実行結果」を確認
2. 実行ユーザーの権限を確認
3. Pythonパスが正しいか確認
4. 絶対パスを使用しているか確認

**修正例:**

```cmd
# Pythonの絶対パスを取得
where python

# タスク作成時に絶対パスを指定
schtasks /create /tn "GitHubIssueWatchdog" /tr "C:\Python310\python.exe C:\Users\Tenormusica\Documents\github-remote-desktop\watchdog_monitor_service.py" /sc minute /mo 5 /ru %USERNAME%
```

---

## 📝 ログファイル

- **watchdog_monitor.log**: Watchdog Monitorの実行ログ
- **self_healing_monitor.log**: Self-Healing Monitorの実行ログ
- **private_issue_monitor.log**: 監視スクリプト本体のログ
- **monitor_service.log**: 配布版v2のログ

定期的にログファイルを確認し、異常がないかチェックしてください。

---

## 🚀 推奨設定

**初心者向け（シンプル）:**
```cmd
# Watchdog Monitorのみ使用
schtasks /create /tn "GitHubIssueWatchdog" /tr "python C:\Users\Tenormusica\Documents\github-remote-desktop\watchdog_monitor_service.py" /sc minute /mo 5 /ru %USERNAME%
```

**上級者向け（最大限の安定性）:**
```cmd
# 1. Watchdog Monitorをタスクスケジューラに登録
schtasks /create /tn "GitHubIssueWatchdog" /tr "python C:\Users\Tenormusica\Documents\github-remote-desktop\watchdog_monitor_service.py" /sc minute /mo 5 /ru %USERNAME%

# 2. Self-Healing Monitor経由で起動（手動またはタスクスケジューラ）
python self_healing_monitor.py private_issue_monitor_service.py
```

---

**作成日**: 2025-01-30  
**対応バージョン**: v2.1.0