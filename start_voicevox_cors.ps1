# VOICEVOX CORS起動スクリプト
Write-Host "VOICEVOX をCORS許可モードで起動します..." -ForegroundColor Cyan

# VOICEVOXの実行ファイルパスを探す
$voicevoxPaths = @(
    "C:\Program Files\VOICEVOX\VOICEVOX.exe",
    "C:\Program Files (x86)\VOICEVOX\VOICEVOX.exe",
    "$env:LOCALAPPDATA\Programs\VOICEVOX\VOICEVOX.exe",
    "C:\Users\$env:USERNAME\AppData\Local\Programs\VOICEVOX\VOICEVOX.exe"
)

$voicevoxPath = $null
foreach ($path in $voicevoxPaths) {
    if (Test-Path $path) {
        $voicevoxPath = $path
        break
    }
}

if (-not $voicevoxPath) {
    Write-Host "❌ VOICEVOXが見つかりません" -ForegroundColor Red
    Write-Host "VOICEVOXのインストール先を確認してください" -ForegroundColor Yellow
    Read-Host "Enterキーを押して終了"
    exit 1
}

Write-Host "✓ VOICEVOX検出: $voicevoxPath" -ForegroundColor Green
Write-Host ""
Write-Host "CORS許可モードで起動中..." -ForegroundColor Cyan

Start-Process -FilePath $voicevoxPath -ArgumentList "--cors_policy_mode=all"

Start-Sleep -Seconds 3

Write-Host ""
Write-Host "✅ VOICEVOX起動完了" -ForegroundColor Green
Write-Host "ブラウザを再読み込みして音声通知をテストしてください" -ForegroundColor Yellow
Read-Host "Enterキーを押して終了"
