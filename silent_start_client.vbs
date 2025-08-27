' Claude Code Remote Desktop - Silent Auto Start
' This VBS script starts the client without showing console windows
Set WshShell = CreateObject("WScript.Shell")

' Start the batch file in hidden mode (window style 0 = hidden)
WshShell.Run """C:\Users\Tenormusica\web-remote-desktop\auto_start_client.bat""", 0, False