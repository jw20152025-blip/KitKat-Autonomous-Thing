# Kittelligence 2.0

A fresh Windows desktop companion for KitKat. The original project remains intact; this version lives in its own folder and reuses the existing artwork in the repository's top-level `assets/` directory.

## Launch

1. Install Python 3.10 or newer from https://www.python.org/downloads/ (enable **Add Python to PATH**).
2. Open `Kittelligence2`.
3. Double-click `launch.bat`.

The launcher creates a local virtual environment, installs dependencies, and starts KitKat. No API key or paid service is required.

## Features

- Animated desktop pet using the existing `assets/idle`, `assets/walk`, `assets/sit`, `assets/sleep`, and `assets/meow` artwork folders.
- Autonomous, explainable behaviour scheduler.
- Drag KitKat around; right-click for the application menu.
- Control Center with live needs and interaction count.
- Persistent memory stored in `%APPDATA%\Kittelligence\memory.json`.
- GitHub Releases update checker. It offers updates only when a newer release includes a Windows `.exe` installer. If GitHub provides an asset SHA-256 digest, the updater verifies it before launching the installer.

## Publishing updates

Build and attach a Windows installer named something like `Kittelligence-Setup.exe` to a GitHub Release. Use a version tag such as `v2.0.1`. The updater checks the repository's latest published release.

The installer should close/replace the application files but must not delete `%APPDATA%\Kittelligence`; that directory contains the user's memory.

## Notes

- The first run needs internet access to install Python packages.
- Tkinter is included with standard Windows Python installations.
- The pet is a local desktop animation. It does not monitor or control other applications.
