@echo off
echo Starting Remote Desktop Server...
echo.

cd /d "C:\Users\Tenormusica\web-remote-desktop"

echo Server starting on port 8093...
echo.
echo Open this URL on your smartphone:
echo   http://localhost:8093  (same PC)
echo   http://192.168.3.3:8093  (same network)
echo.
echo Starting server now...
python local_server.py --port 8093

echo.
echo Server stopped.
pause