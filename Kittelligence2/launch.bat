@echo off
setlocal
cd /d "%~dp0"
title Kittelligence 2.0 Launcher

where py >nul 2>nul
if errorlevel 1 (
  echo Python 3 is required. Install it from https://www.python.org/downloads/
  echo Make sure "Add Python to PATH" is selected.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Creating Kittelligence environment...
  py -3 -m venv .venv
  if errorlevel 1 goto failed
)

echo Installing or updating required packages...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed

echo Starting KitKat...
".venv\Scripts\python.exe" main.py
if errorlevel 1 goto failed
exit /b 0

:failed
echo.
echo Kittelligence could not start. Review the message above.
pause
exit /b 1
