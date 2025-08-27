# Claude Code Remote Desktop - Auto Startup Setup
# This script sets up automatic startup for the remote desktop client

Write-Host "Setting up Claude Code Remote Desktop Auto Startup..." -ForegroundColor Green

# Paths
$ClientBatPath = "C:\Users\Tenormusica\web-remote-desktop\auto_start_client.bat"
$StartupFolder = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup"
$ShortcutPath = "$StartupFolder\Claude Remote Desktop.lnk"

# Create Windows shortcut for startup
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $ClientBatPath
$Shortcut.WorkingDirectory = "C:\Users\Tenormusica\web-remote-desktop"
$Shortcut.Description = "Claude Code Remote Desktop Auto Start"
$Shortcut.Save()

Write-Host "✅ Startup shortcut created: $ShortcutPath" -ForegroundColor Green

# Also create a desktop shortcut for manual control
$DesktopPath = "$env:USERPROFILE\Desktop\Claude Remote Desktop.lnk"
$DesktopShortcut = $WshShell.CreateShortcut($DesktopPath)
$DesktopShortcut.TargetPath = $ClientBatPath
$DesktopShortcut.WorkingDirectory = "C:\Users\Tenormusica\web-remote-desktop"
$DesktopShortcut.Description = "Claude Code Remote Desktop Manual Start"
$DesktopShortcut.Save()

Write-Host "✅ Desktop shortcut created: $DesktopPath" -ForegroundColor Green

Write-Host "`n🎉 Setup Complete!" -ForegroundColor Yellow
Write-Host "The Claude Code Remote Desktop client will now:" -ForegroundColor White
Write-Host "  • Start automatically when Windows boots" -ForegroundColor White
Write-Host "  • Restart automatically if it crashes" -ForegroundColor White
Write-Host "  • Can be started manually from desktop shortcut" -ForegroundColor White
Write-Host "`n📱 Web Interface: https://remote-desktop-ycqe3vmjva-uc.a.run.app" -ForegroundColor Cyan
Write-Host "`nTo disable auto-startup, delete: $ShortcutPath" -ForegroundColor Gray