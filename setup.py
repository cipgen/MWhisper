"""
MWhisper py2app setup script
Creates a standalone macOS application
"""

from setuptools import setup

APP = ['main.py']
DATA_FILES = [
    ('assets', ['assets/icon_idle.png', 'assets/icon_active.png', 'assets/icon_ready.png']),
    ('.', ['config.json']),
]

OPTIONS = {
    'argv_emulation': False,
    'iconfile': 'assets/icon_idle.png',  # Will be converted to .icns if needed
    'plist': {
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
    'packages': [
        'parakeet_mlx',
        'mlx',
        'mlx_lm',
        'rumps',
        'pynput',
        'numpy',
        'sounddevice',
        'soundfile',
        'huggingface_hub',
        'transformers',
    ],
    'includes': [
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
    ],
}

setup(
    name='MWhisper',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
