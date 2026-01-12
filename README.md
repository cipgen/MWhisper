# MWhisper - Voice Dictation for Mac

🎤 Local voice dictation using [Parakeet-MLX](https://github.com/senstella/parakeet-mlx) (NVIDIA Parakeet-TDT-0.6B-v3), optimized for Apple Silicon.

## Features

- 🎤 **Real-time voice transcription** — powered by Parakeet-MLX
- ⌨️ **Global hotkey** — ⌘⇧D (Cmd+Shift+D) to start/stop recording
- 📝 **Auto-insert text** — pastes transcribed text into any active window
- 🌍 **25 languages** with auto-detection
- 🧹 **Filler word removal** — removes "uh", "um", etc.
- 📊 **Menu Bar app** — status indicator and controls
- 📜 **Dictation history** — stores last 20 transcriptions
- ⚙️ **Customizable hotkey** — change via menu "Change Hotkey..."

## Requirements

- macOS (Apple Silicon M1/M2/M3/M4)
- Python 3.10+
- ffmpeg (for audio processing)

## Installation

```bash
# Clone repository
git clone https://github.com/your-repo/MWhisper.git
cd MWhisper

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install ffmpeg
brew install ffmpeg

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Run from source:
```bash
source venv/bin/activate
python main.py
```

### Build standalone app:
```bash
source venv/bin/activate
pyinstaller --clean --noconfirm MWhisper.spec
cp -R dist/MWhisper.app /Applications/
```

### Controls:
- **⌘⇧D** (Cmd+Shift+D) — Start/stop recording
- **Menu Bar Icon** — Access history, settings, change hotkey

## Permissions Required

MWhisper requires the following macOS permissions:

| Permission | Purpose |
|------------|---------|
| **Accessibility** | Text insertion via keyboard simulation |
| **Input Monitoring** | Global hotkey detection |
| **Microphone** | Voice recording |

Go to: **System Settings → Privacy & Security** to grant permissions.

## Configuration

Settings are stored in `config.json`:

```json
{
    "hotkey": "<cmd>+<shift>+d",
    "microphone_id": null,
    "language": "auto",
    "filter_fillers": true,
    "history_size": 20
}
```

## Debug Logs

Logs are written to `~/Desktop/mwhisper_debug.log` when running the .app bundle.

## Known Limitations

- **Code-switching** (mixing languages in one phrase) is not supported by Parakeet-MLX
- English words spoken while in "Russian mode" will be transliterated (e.g., "hello" → "хелоу")

## License

MIT
