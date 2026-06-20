@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-devspace-tunnel.ps1"
echo.
echo Press any key to close this launcher window.
pause >nul
