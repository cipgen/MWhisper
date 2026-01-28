# MWhisper Installation Guide

## Requirements

- **Python 3.10–3.12** (recommended: 3.11)
- macOS with Apple Silicon (M1/M2/M3) for parakeet-mlx

---

## macOS (Apple Silicon M1/M2/M3)

### Check Python version first

```bash
python3 --version
```

If version is **not** 3.10–3.12, install correct version:

```bash
# Install pyenv (Python version manager)
brew install pyenv

# Add pyenv to shell (add to ~/.zshrc)
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
echo 'eval "$(pyenv init -)"' >> ~/.zshrc
source ~/.zshrc

# Install Python 3.11
pyenv install 3.11.9
pyenv global 3.11.9

# Verify
python --version  # Should show 3.11.9
```

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/MWhisper.git
cd MWhisper

# 2. Install FFmpeg (required for audio processing)
brew install ffmpeg

# 3. Create virtual environment with correct Python
python3.11 -m venv venv
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Create config file
cp config.example.json config.json

# 6. (Optional) Add OpenAI API key for translation
# Edit config.json and set "openai_api_key": "sk-..."

# 7. Run the app
python main.py
```

### macOS Permissions Required

Go to **System Settings → Privacy & Security** and enable:
- **Accessibility** — for text insertion
- **Input Monitoring** — for global hotkeys
- **Microphone** — for voice recording

---

## Build Standalone .app (macOS)

To create a standalone application that runs without terminal:

```bash
# 1. Activate venv
source venv/bin/activate

# 2. Install PyInstaller
pip install pyinstaller

# 3. Clean previous builds
rm -rf build dist

# 4. Build .app bundle
pyinstaller --clean --noconfirm MWhisper.spec

# 5. Run the built app
open dist/MWhisper.app

# 6. (Optional) Install to Applications
cp -R dist/MWhisper.app /Applications/
```

The `.app` bundle will be in `dist/MWhisper.app`.

---

## Linux (Ubuntu/Debian)

> ⚠️ **Note:** Parakeet-MLX requires Apple Silicon. On Linux, you need to replace it with an alternative transcription backend.

```bash
# 1. Install system dependencies
sudo apt update
sudo apt install -y python3 python3-venv python3-pip ffmpeg portaudio19-dev

# 2. Clone the repository
git clone https://github.com/YOUR_USERNAME/MWhisper.git
cd MWhisper

# 3. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# 4. Install Python dependencies
pip install -r requirements.txt

# 5. Create config file
cp config.example.json config.json

# 6. (Optional) Add OpenAI API key for translation
# Edit config.json and set "openai_api_key": "sk-..."

# 7. Run the app
python main.py
```

### Linux Notes

- `portaudio19-dev` is required for `sounddevice`
- For Wayland: may need `xdotool` or `ydotool` for text insertion
- Some features (rumps menu bar) are macOS-specific

---

## Hotkeys (Default)

| Mode | Hotkey | Description |
|------|--------|-------------|
| Dictation | `Ctrl + 1` | Speech → Text |
| Translate | `Ctrl + 2` | Speech → English |
| Smart Fix | `Cmd + Shift + E` | Fix grammar |

Hotkeys can be changed in Settings (menu bar icon).
