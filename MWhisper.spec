# -*- mode: python ; coding: utf-8 -*-
"""
MWhisper PyInstaller spec file
Creates a standalone macOS application
"""

import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_all

block_cipher = None

# Get the project root
project_root = os.path.dirname(os.path.abspath(SPEC))


# Collect all resources for parakeet_mlx and mlx
tmp_ret_parakeet = collect_all('parakeet_mlx')
tmp_ret_mlx = collect_all('mlx')

datas = tmp_ret_parakeet[0] + tmp_ret_mlx[0]
binaries = tmp_ret_parakeet[1] + tmp_ret_mlx[1]
hiddenimports = tmp_ret_parakeet[2] + tmp_ret_mlx[2]

# Add FFmpeg binary for parakeet-mlx audio loading
import shutil
ffmpeg_path = shutil.which('ffmpeg')
if ffmpeg_path:
    binaries.append((ffmpeg_path, '.'))

a = Analysis(
    ['main.py'],
    pathex=[project_root],
    binaries=binaries,
    datas=datas + [
        ('assets/app_icon.png', 'assets'),
        ('assets/menu_icon_idle.png', 'assets'),
        ('assets/menu_icon_active.png', 'assets'),
        ('assets/menu_icon_ready.png', 'assets'),
        ('config.json', '.'),
        ('src', 'src'),
    ],
    hiddenimports=hiddenimports + [
        'mlx',
        'mlx.core',
        'mlx.nn',
        'rumps',
        'pynput',
        'pynput.keyboard',
        'pynput.keyboard._darwin',
        'numpy',
        'sounddevice',
        'soundfile',
        'huggingface_hub',
        'transformers',
        'librosa',
        'dacite',
        'typer',
        'src',
        'src.app',
        'src.audio_capture',
        'src.transcriber',
        'src.filler_filter',
        'src.hotkeys',
        'src.text_inserter',
        'src.settings',
        'src.history',
        'src.menu_bar',
        'PySide6',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'pynput',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MWhisper',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MWhisper',
)

app = BUNDLE(
    coll,
    name='MWhisper.app',
    icon='assets/app_icon.png',
    bundle_identifier='com.mwhisper.app',
    info_plist={
        'CFBundleName': 'MWhisper',
        'CFBundleDisplayName': 'MWhisper',
        'CFBundleIdentifier': 'com.mwhisper.app',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'LSMinimumSystemVersion': '11.0',
        'NSHighResolutionCapable': True,
        'LSUIElement': True,  # Menu bar app, no dock icon
        # Required permissions
        'NSMicrophoneUsageDescription': 'MWhisper needs microphone access to record your voice for dictation.',
        'NSAppleEventsUsageDescription': 'MWhisper needs to send keystrokes to insert dictated text.',
    },
)
