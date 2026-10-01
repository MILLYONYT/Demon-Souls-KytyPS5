@echo off
cd /d "%~dp0"
python -c "import numpy" >nul 2>nul
if errorlevel 1 (
  echo Install Python 3.11 or newer and run: python -m pip install numpy
  pause
  exit /b 1
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0precompile-windows.ps1" %*
pause
