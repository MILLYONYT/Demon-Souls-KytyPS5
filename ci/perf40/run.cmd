@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run-windows.ps1" -Prompt %*
if errorlevel 1 pause
