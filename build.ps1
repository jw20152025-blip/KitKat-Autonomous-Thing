$ErrorActionPreference = "Stop"

$Root = $PSScriptRoot
$Build = Join-Path $Root "build"
$Dist = Join-Path $Root "dist"
$Installer = Join-Path $Root "installer"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "       KITTELLIGENCE RELEASE BUILD" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# -----------------------------------------
# CHECKS
# -----------------------------------------

Write-Host "[1/6] Checking project..." -ForegroundColor Yellow

if (-not (Test-Path "$Root\main.py")) {
    throw "main.py was not found."
}

if (-not (Test-Path "$Root\assets")) {
    throw "assets folder was not found."
}

if (-not (Test-Path "$Root\sounds")) {
    throw "sounds folder was not found."
}

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    throw "Python launcher 'py' was not found."
}

py --version

Write-Host ""
Write-Host "[2/6] Checking PyInstaller..." -ForegroundColor Yellow

py -m PyInstaller --version

if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller is not installed."
}

# -----------------------------------------
# STOP OLD INSTANCES
# -----------------------------------------

Write-Host ""
Write-Host "[3/6] Closing old Kittelligence processes..." -ForegroundColor Yellow

Get-Process Kittelligence -ErrorAction SilentlyContinue |
    Stop-Process -Force -ErrorAction SilentlyContinue

Get-Process KittelligenceDebug -ErrorAction SilentlyContinue |
    Stop-Process -Force -ErrorAction SilentlyContinue

Start-Sleep -Milliseconds 500

# -----------------------------------------
# CLEAN
# -----------------------------------------

Write-Host ""
Write-Host "[4/6] Cleaning old builds..." -ForegroundColor Yellow

if (Test-Path $Build) {
    Remove-Item $Build -Recurse -Force
}

if (Test-Path $Dist) {
    Remove-Item $Dist -Recurse -Force
}

if (Test-Path $Installer) {
    Remove-Item $Installer -Recurse -Force
}

New-Item -ItemType Directory $Installer -Force | Out-Null

# -----------------------------------------
# BUILD ONEDIR
# -----------------------------------------

Write-Host ""
Write-Host "[5/6] Building Kittelligence..." -ForegroundColor Yellow
Write-Host ""

py -m PyInstaller `
    --noconfirm `
    --clean `
    --onedir `
    --windowed `
    --name "Kittelligence" `
    --collect-all "PIL" `
    --collect-all "pystray" `
    --hidden-import="PIL.ImageTk" `
    --hidden-import="pystray._win32" `
    --add-data "assets;assets" `
    --add-data "sounds;sounds" `
    main.py

if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller failed."
}

# -----------------------------------------
# VERIFY ONEDIR
# -----------------------------------------

$AppDir = Join-Path $Dist "Kittelligence"
$Exe = Join-Path $AppDir "Kittelligence.exe"

if (-not (Test-Path $Exe)) {
    throw "Kittelligence.exe was not created."
}

if (-not (Test-Path $AppDir)) {
    throw "Kittelligence application directory was not created."
}

Write-Host ""
Write-Host "BUILD SUCCESSFUL" -ForegroundColor Green
Write-Host ""
Write-Host "Application:"
Write-Host "  $AppDir"
Write-Host ""

# -----------------------------------------
# TEST BEFORE INSTALLER
# -----------------------------------------

Write-Host "Testing packaged application..." -ForegroundColor Yellow
Write-Host ""
Write-Host "Launching:"
Write-Host "  $Exe"
Write-Host ""

Start-Process -FilePath $Exe -WorkingDirectory $AppDir

Start-Sleep -Seconds 5

$Running = Get-Process Kittelligence -ErrorAction SilentlyContinue

if (-not $Running) {
    Write-Host ""
    Write-Host "WARNING: Kittelligence exited during the test." -ForegroundColor Red
    Write-Host "The installer will NOT be created." -ForegroundColor Red
    exit 1
}

Write-Host "Kittelligence launched successfully." -ForegroundColor Green

# Don't leave test copy running.
$Running | Stop-Process -Force -ErrorAction SilentlyContinue

# -----------------------------------------
# BUILD INSTALLER
# -----------------------------------------

Write-Host ""
Write-Host "[6/6] Building installer..." -ForegroundColor Yellow

$ISCCCandidates = @(
    "$env:ProgramFiles(x86)\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
)

$ISCC = $null

foreach ($Candidate in $ISCCCandidates) {
    if (Test-Path $Candidate) {
        $ISCC = $Candidate
        break
    }
}

if (-not $ISCC) {
    throw "Inno Setup 6 (ISCC.exe) was not found."
}

& $ISCC "$Root\installer.iss"

if ($LASTEXITCODE -ne 0) {
    throw "Inno Setup failed."
}

$InstallerFile = Get-ChildItem `
    $Installer `
    -Filter "*.exe" `
    -File |
    Select-Object -First 1

if (-not $InstallerFile) {
    throw "Installer was not created."
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "          BUILD COMPLETE" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

Write-Host "App:"
Write-Host "  $Exe"

Write-Host ""
Write-Host "Installer:"
Write-Host "  $($InstallerFile.FullName)"

Write-Host ""