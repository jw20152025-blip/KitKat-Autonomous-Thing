# Kittelligence 2.1

A Windows desktop companion for KitKat. The original project remains intact; Kittelligence 2.1 lives in this folder and reuses the artwork and WAV sounds in the repository.

## Launch

1. Install Python 3.10 or newer from https://www.python.org/downloads/ and enable Add Python to PATH.
2. Open the Kittelligence2 folder.
3. Double-click launch.bat.

The launcher creates a local virtual environment, installs dependencies, and starts KitKat.

## Features

- Animated, draggable desktop pet with a transparent background and magenta-fringe cleanup.
- Real WAV meow playback from sounds/meow/meow.wav using Windows audio playback.
- Purr playback from sounds/purr/purr.wav.
- Autonomous behaviour and persistent memory.
- Scrollable care centre with hunger, hydration, energy, happiness, boredom, and litter cleanliness.
- Care actions: feed, water, play, nap, clean litter, brush, pet, meow, and purr.
- A KitKat-themed local chat assistant that can answer care questions and perform care actions.
- The assistant can open automatically when an important need becomes urgent.
- Memory saved to %APPDATA%\Kittelligence\memory.json.
- GitHub Releases update checker.

## Assistant

The assistant is an offline, intent-aware helper. It does not require an API key, paid subscription, or internet connection, and it can change KitKat's in-app care stats. It is not a general-purpose cloud language model.

## Build a Windows installer

Run launch.bat once, then run build.bat. Install Inno Setup 6 to produce Kittelligence-Setup.exe. The build includes both assets and sounds so audio works in the packaged application.

The installer must not delete %APPDATA%\Kittelligence because that folder contains saved memory.
