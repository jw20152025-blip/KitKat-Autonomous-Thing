@echo off

title Kiteelegence Builder

echo.
echo ==============================
echo       KITEELEGENCE BUILD
echo ==============================
echo.

if not exist .venv (
    python -m venv .venv
)

call .venv\Scripts\activate.bat

python -m pip install --upgrade pip
pip install -r requirements.txt

if exist build (
    rmdir /s /q build
)

if exist dist (
    rmdir /s /q dist
)

if exist Kiteelegence.spec (
    del /q Kiteelegence.spec
)

pyinstaller ^
    --noconfirm ^
    --clean ^
    --onedir ^
    --windowed ^
    --name Kiteelegence ^
    --add-data "assets;assets" ^
    --add-data "sounds;sounds" ^
    main.py

echo.
echo ==============================
echo BUILD FINISHED
echo ==============================
echo.
echo dist\Kiteelegence\Kiteelegence.exe
echo.

pause