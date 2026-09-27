@echo off
title Building Kittelligence

echo.
echo ================================
echo       KITELLIGENCE BUILDER
echo ================================
echo.

call .venv\Scripts\activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller

echo.
echo Cleaning old builds...

rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
del /q Kiteelegence.spec 2>nul

echo.
echo Building Kittelligence...

pyinstaller ^
    --onedir ^
    --windowed ^
    --name Kiteelegence ^
    --add-data "assets;assets" ^
    --add-data "sounds;sounds" ^
    main.py

echo.
echo ================================
echo        BUILD COMPLETE
echo ================================
echo.
echo Output:
echo dist\Kiteelegence\
echo.

pause