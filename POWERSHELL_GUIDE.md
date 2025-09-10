# PowerShell起動ガイド

## 📁 ディレクトリ情報
**固定ディレクトリ**: `C:\Users\Tenormusica\cc-snap-to-github`

すべてのファイルがこのディレクトリに配置されています：
- `Start-BackgroundMonitor.ps1` - PowerShell起動スクリプト
- `persistent_service.py` - 永続監視サービス本体
- `gh_issue_to_claude_paste.py` - メイン処理エンジン
- `logs/` - ログファイル保存ディレクトリ

## 🚀 PowerShell起動方法

### **方法1: PowerShellから直接実行**
```powershell
# ディレクトリに移動
cd "C:\Users\Tenormusica\cc-snap-to-github"

# バックグラウンドサービス開始
.\Start-BackgroundMonitor.ps1
```

### **方法2: フルパス指定で実行**
```powershell
# どのディレクトリからでも実行可能
& "C:\Users\Tenormusica\cc-snap-to-github\Start-BackgroundMonitor.ps1"
```

### **方法3: PowerShell管理者モードで実行**
```powershell
# 管理者権限で実行（推奨）
Start-Process PowerShell -ArgumentList "-File C:\Users\Tenormusica\cc-snap-to-github\Start-BackgroundMonitor.ps1" -Verb RunAs
```

## ⚙️ 管理コマンド

### **システム状態確認**
```powershell
.\Start-BackgroundMonitor.ps1 -ShowStatus
```
- 稼働中プロセスの確認
- 稼働時間の表示
- 最新ログファイルの確認
- 処理済みコメントID表示

### **ログファイル確認**
```powershell
.\Start-BackgroundMonitor.ps1 -Logs
```
- 全ログファイル一覧表示
- ファイルサイズと更新日時表示
- 最新ログの表示コマンド提供

### **サービス停止**
```powershell
.\Start-BackgroundMonitor.ps1 -Stop
```
- 全バックグラウンドプロセスを安全停止
- プロセスID表示付き

### **最新ログのリアルタイム表示**
```powershell
Get-Content logs\comment_monitor_$(Get-Date -Format 'yyyyMMdd').log -Tail 10 -Wait
```

## 🔧 実行環境設定

### **PowerShell実行ポリシーの設定** (初回のみ)
```powershell
# 管理者権限で実行
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### **ディレクトリ確認**
```powershell
# ディレクトリの存在確認
Test-Path "C:\Users\Tenormusica\cc-snap-to-github"

# ディレクトリ内容確認
Get-ChildItem "C:\Users\Tenormusica\cc-snap-to-github"
```

## 📊 システム動作確認

### **プロセス確認**
```powershell
# Python監視プロセスの確認
Get-Process | Where-Object { $_.ProcessName -eq "python" }

# 詳細情報付きプロセス確認
Get-WmiObject Win32_Process | Where-Object { $_.CommandLine -like "*persistent_service.py*" }
```

### **ログモニタリング**
```powershell
# 今日のログをリアルタイム監視
Get-Content "C:\Users\Tenormusica\cc-snap-to-github\logs\comment_monitor_$(Get-Date -Format 'yyyyMMdd').log" -Tail 0 -Wait
```

## 🎯 ワンクリック起動用ショートカット

### **デスクトップショートカット作成**
```powershell
# デスクトップにショートカット作成
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\GitHub Comment Monitor.lnk")
$Shortcut.TargetPath = "powershell.exe"
$Shortcut.Arguments = "-WindowStyle Hidden -File `"C:\Users\Tenormusica\cc-snap-to-github\Start-BackgroundMonitor.ps1`""
$Shortcut.WorkingDirectory = "C:\Users\Tenormusica\cc-snap-to-github"
$Shortcut.IconLocation = "shell32.dll,25"
$Shortcut.Save()
```

## 🚀 推奨起動手順

1. **PowerShellを管理者権限で開く**
2. **実行ポリシーを設定** (初回のみ)
   ```powershell
   Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```
3. **ディレクトリに移動**
   ```powershell
   cd "C:\Users\Tenormusica\cc-snap-to-github"
   ```
4. **サービス開始**
   ```powershell
   .\Start-BackgroundMonitor.ps1
   ```

## ✅ 成功確認

サービスが正常に開始されると、以下が表示されます：
```
✅ バックグラウンドサービス開始完了！
   プロセスID: 1234
   開始時刻: 2025/08/29 00:30:15

🎯 監視対象: GitHub Issue #3
⏱️ 監視間隔: 5秒
📁 ログ保存先: C:\Users\Tenormusica\cc-snap-to-github\logs\

🎉 GitHub Issue #3のコメントが24時間365日自動処理されます！
```

これで**PowerShellから完全にバックグラウンドで永続監視システムが稼働**します！