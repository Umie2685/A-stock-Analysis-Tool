@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0stop-cloudflared.ps1"
echo.
echo Press any key to close this window.
pause >nul
