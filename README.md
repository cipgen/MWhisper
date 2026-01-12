# MWhisper - Voice Dictation Application for Mac M1

Local voice dictation using Parakeet-MLX (NVIDIA Parakeet-TDT-0.6B-v3) optimized for Apple Silicon.

## Features

- 🎤 Real-time voice transcription
- ⌨️ Global hotkey activation (Cmd+Shift+D)
- 📝 Auto-insert text into active window
- 🌍 25 languages with auto-detection
- 🧹 Filler word removal ("uh", "um", etc.)
- 📊 Menu Bar status indicator
- 📜 Dictation history

## Requirements

- macOS (Apple Silicon M1/M2/M3)
- Python 3.10+
- ffmpeg (for audio processing)

## Installation

```bash
# Install ffmpeg
brew install ffmpeg

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

- **Cmd+Shift+D** — Start/stop recording
- Click Menu Bar icon for settings and history

## Accessibility Permission

This app requires Accessibility permission for global hotkeys.
Go to: System Preferences → Security & Privacy → Privacy → Accessibility
