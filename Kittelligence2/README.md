# Kittelligence 2.2

A Windows desktop companion for KitKat. The original project remains intact; Kittelligence 2 lives in this folder and reuses the artwork and WAV sounds in the repository.

## Launch

1. Install Python 3.10 or newer from https://www.python.org/downloads/ and enable Add Python to PATH.
2. Open the Kittelligence2 folder.
3. Double-click launch.bat.

The launcher creates a local virtual environment, installs dependencies, and starts KitKat.

## Features

- Animated, draggable desktop pet with a transparent background and magenta-fringe cleanup.
- WAV meow and purr playback through Windows audio.
- Autonomous behaviour and persistent memory.
- Scrollable care centre with hunger, hydration, energy, happiness, boredom, and litter cleanliness.
- Care actions: feed, water, play, nap, clean litter, brush, pet, meow, and purr.
- A genuinely generative KitKat chat assistant powered by a local language model.
- The assistant receives KitKat's current care stats as conversation context.
- The assistant can open automatically when an important need becomes urgent.
- Chat history is kept in memory for the current app session.
- Care memory saved to %APPDATA%\Kittelligence\\memory.json.
- GitHub Releases update checker.

## Set up KitKat AI (one-time)

Kittelligence uses Ollama to run Qwen 2.5 1.5B locally. This is a real language model, not a list of keyword responses. Chat requests stay on this computer and do not require an API key or paid AI service.

1. Install Ollama for Windows from https://ollama.com/download.
2. Open PowerShell and download the model:

   ```powershell
   ollama pull qwen2.5:1.5b
   ```

3. Leave the Ollama app running in the background.
4. Start Kittelligence with launch.bat and open Chat with KitKat.

The first response can take longer while the model loads. This small model is selected to fit a PC with limited graphics memory; it may respond more slowly when running on the CPU.

## Privacy and limitations

The model runs locally through Ollama at 127.0.0.1:11434. Kittelligence sends the chat and current care stats to that local service; it does not send them to a hosted AI provider. Conversation history is currently kept only until Kittelligence closes. The AI can discuss care and make suggestions, while the care buttons remain the controls that actually change KitKat's stats.

## Build a Windows installer

Run launch.bat once, then run build.bat. Install Inno Setup 6 to produce Kittelligence-Setup.exe. The build includes both assets and sounds so audio works in the packaged application.

The installer must not delete %APPDATA%\Kittelligence because that folder contains saved memory.
