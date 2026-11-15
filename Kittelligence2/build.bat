@echo off
setlocal
cd /d "%~dp0"
title Build Kittelligence 2.1

if not exist ".venv\Scripts\python.exe" (
  echo Run launch.bat once first so the environment is created.
  pause
  exit /b 1
)

echo Building the Windows application...
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --windowed --onedir --name Kittelligence --add-data "..\assets;assets" --add-data "..\sounds;sounds" main.py
if errorlevel 1 goto failed

where ISCC >nul 2>nul
if errorlevel 1 (
  echo.
  echo Portable build created in dist\Kittelligence.
  echo To create the Setup.exe, install Inno Setup 6 and run this file again.
  pause
  exit /b 0
)

ISCC installer.iss
if errorlevel 1 goto failed

echo.
echo Installer created: dist\Kittelligence-Setup.exe
pause
exit /b 0

:failed
echo Build failed. Read the error above.
pause
exit /b 1
