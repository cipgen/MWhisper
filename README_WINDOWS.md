# MWhisper for Windows 🎤

Voice dictation application that runs in the system tray on Windows. Speak into your microphone and have your speech transcribed and inserted into any application.

## Features

- **Push-to-Talk Dictation**: Hold a hotkey to record, release to transcribe and insert
- **High-Quality Transcription**: Uses faster-whisper (Whisper) for accurate speech recognition
- **System Tray Integration**: Runs quietly in the background
- **Automatic Text Insertion**: Transcribed text is automatically pasted into your active application
- **OpenAI Translation**: Optional translation feature using OpenAI API
- **Custom Actions**: Create custom hotkeys with different prompts

---

## Installation

### Prerequisites

1. **Python 3.10+** - Download from [python.org](https://www.python.org/downloads/)
2. **CUDA (Recommended)** - For faster transcription with GPU. Download from [NVIDIA](https://developer.nvidia.com/cuda-downloads)
   - Without CUDA, transcription will use CPU (slower but works)

### Step 1: Clone or Download

```bash
git clone https://github.com/yourusername/MWhisper.git
cd MWhisper
```

### Step 2: Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements-windows.txt
```

> **Note**: If you have an NVIDIA GPU, install PyTorch with CUDA support:
> ```bash
> pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
> ```

### Step 4: Run MWhisper

```bash
python main.py
```

---

## Usage

### Default Hotkey

| Action | Hotkey |
|--------|--------|
| **Dictate** | `Ctrl + Shift + D` |
| **Translate** | `Ctrl + Shift + T` |
| **Smart Fix** | `Ctrl + Shift + E` |

1. **Hold** the hotkey to start recording
2. **Speak** into your microphone
3. **Release** the hotkey to transcribe and insert text

### System Tray

After launching, MWhisper appears in your system tray (bottom-right corner):

- **Left-click** on the icon to see the menu
- **Green icon** = Ready
- **Red icon** = Recording
- **Yellow icon** = Processing

### Settings

Access settings from the tray menu → Settings:

- **Microphone**: Select input device
- **Hotkey**: Change the recording hotkey
- **Language**: Set transcription language
- **OpenAI API Key**: For translation feature

---

## Configuration

Settings are stored in `config.json`:

```json
{
    "hotkey": "<ctrl>+<shift>+d",
    "translate_hotkey": "<ctrl>+<shift>+t",
    "fix_hotkey": "<ctrl>+<shift>+e",
    "language": "auto",
    "microphone_id": null,
    "filter_fillers": true,
    "openai_api_key": ""
}
```

---

## Troubleshooting

### "No module named 'faster_whisper'"

```bash
pip install faster-whisper
```

### "pyautogui.FailSafeException"

PyAutoGUI has a fail-safe that triggers if the mouse is in a corner. Move your mouse away from screen corners before using.

### Slow transcription (no GPU)

Install PyTorch with CUDA support:
```bash
pip install torch --index-url https://download.pytorch.org/whl/cu121
```

### No audio detected

1. Check Windows Sound Settings → Recording devices
2. Make sure your microphone is selected as default
3. Test microphone in Windows Settings

### Hotkey not working

1. Try running as Administrator
2. Some fullscreen applications may block global hotkeys
3. Try a different hotkey combination

---

## Building Executable (Optional)

To create a standalone `.exe`:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name MWhisper main.py
```

The executable will be in the `dist` folder.

---

## Differences from macOS Version

| Feature | macOS | Windows |
|---------|-------|---------|
| Transcription | Parakeet-MLX | faster-whisper |
| Menu Bar | rumps | pystray |
| Text Insertion | Quartz/AppKit | pyautogui |
| Default Hotkey | ⌘⇧D | Ctrl+Shift+D |

---

## Requirements

- Windows 10/11
- Python 3.10+
- Microphone
- NVIDIA GPU with CUDA (recommended for fast transcription)

---

## License

MIT License
