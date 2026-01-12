# MWhisper - Voice Dictation for Mac

🎤 Local voice dictation using [Parakeet-MLX](https://github.com/senstella/parakeet-mlx) (NVIDIA Parakeet-TDT-0.6B-v3), optimized for Apple Silicon.

## Features

## Features

- 🎤 **Real-time voice transcription** — powered by Parakeet-MLX
- 🌐 **Voice Translation** — Translates speech to English (configurable) via OpenAI
- ✨ **Smart Fix** — Corrects grammar and style without translating (preserves language)
- ⌨️ **Push-to-Talk Hotkeys** — 3 distinct hotkeys for different modes
- 📝 **Auto-insert text** — Pastes text into any active window (Word, browser, messengers)
- ⚙️ **Customizable Prompts** — Tweak system prompts for translation and grammar correction
- 📊 **Menu Bar app** — Status indicator and quick settings
- 📜 **Dictation history** — Stores last 20 transcriptions

## Usage

### 🚀 How to Run (Development)
To run the app directly from python source:

```bash
# activate virtual environment
source venv/bin/activate

# run main script
python main.py
```

### 📦 How to Build (Release Version)
To build a standalone `.app` bundle that runs without a terminal:

```bash
# 1. Kill any running instance
pkill -9 MWhisper

# 2. Clean previous build artifacts
rm -rf build dist

# 3. Activate venv
source venv/bin/activate

# 4. Build with PyInstaller
pyinstaller --clean --noconfirm MWhisper.spec

# 5. Install to Applications (Optional)
rm -rf /Applications/MWhisper.app
cp -R dist/MWhisper.app /Applications/
```

### 🎮 Controls (Default Hotkeys)
| Mode | Hotkey | Description |
|------|--------|-------------|
| **Dictation** | `Ctrl + 1` | Speech to Text (Exact) |
| **Translate** | `Ctrl + 2` | Speech to English Text |
| **Smart Fix** | `Cmd + Shift + E` | Fix Grammar & Style (No translate) |

> **Note:** You can customize any of these hotkeys in **Settings** via the menu bar icon.

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
