@echo off
setlocal
cd /d "%~dp0..\.."
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0install-gta5e-visual-pack.ps1" -LaunchReShadeSetup
pause
