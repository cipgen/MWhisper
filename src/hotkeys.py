"""
MWhisper Hotkey Manager
Global hotkeys for macOS using pynput
"""

from pynput import keyboard
from typing import Callable, Optional, Set
import threading
import subprocess


class HotkeyManager:
    """Manages global hotkeys for the application"""
    
    # Key name mappings for display
    KEY_DISPLAY_NAMES = {
        'cmd': '⌘',
        'ctrl': '⌃',
        'alt': '⌥',
        'shift': '⇧',
        'space': 'Space',
    }
    
    def __init__(
        self,
        callback: Callable[[], None],
        hotkey: str = "<cmd>+<shift>+d"
    ):
        """
        Initialize hotkey manager.
        
        Args:
            callback: Function to call when hotkey is pressed
            hotkey: Hotkey combination string (pynput format)
        """
        self.callback = callback
        self.hotkey_string = hotkey
        self._listener: Optional[keyboard.GlobalHotKeys] = None
        self._is_running = False
        self._lock = threading.Lock()
    
    def start(self) -> None:
        """Start listening for hotkeys"""
        with self._lock:
            if self._is_running:
                return
            
            try:
                self._listener = keyboard.GlobalHotKeys({
                    self.hotkey_string: self._on_hotkey
                })
                self._listener.start()
                self._is_running = True
                print(f"⌨️  Hotkey listener started: {self.get_display_string()}")
                
                # Open Input Monitoring settings to remind user
                print("\n⚠️  Hotkeys require Input Monitoring permission!")
                print("If hotkeys don't work, add MWhisper to:")
                print("System Settings → Privacy & Security → Input Monitoring")
                self._open_input_monitoring()
                
            except Exception as e:
                print(f"Failed to start hotkey listener: {e}")
                self._open_input_monitoring()
                raise
    
    def _open_input_monitoring(self):
        """Open Input Monitoring settings"""
        try:
            subprocess.run([
                'open',
                'x-apple.systempreferences:com.apple.preference.security?Privacy_ListenEvent'
            ])
        except:
            pass
    
    def stop(self) -> None:
        """Stop listening for hotkeys"""
        with self._lock:
            if self._listener:
                self._listener.stop()
                self._listener = None
            self._is_running = False
            print("⌨️  Hotkey listener stopped")
    
    def _on_hotkey(self) -> None:
        """Called when hotkey is pressed"""
        print(f"🔥 HOTKEY TRIGGERED: {self.hotkey_string}")
        try:
            self.callback()
        except Exception as e:
            print(f"Hotkey callback error: {e}")
    
    def set_hotkey(self, hotkey: str) -> None:
        """Change the hotkey combination."""
        was_running = self._is_running
        if was_running:
            self.stop()
        
        self.hotkey_string = hotkey
        
        if was_running:
            self.start()
    
    def get_display_string(self) -> str:
        """Get human-readable hotkey string"""
        parts = self.hotkey_string.lower().replace('<', '').replace('>', '').split('+')
        display_parts = []
        
        for part in parts:
            part = part.strip()
            if part in self.KEY_DISPLAY_NAMES:
                display_parts.append(self.KEY_DISPLAY_NAMES[part])
            else:
                display_parts.append(part.upper())
        
        return ''.join(display_parts)
    
    def is_running(self) -> bool:
        """Check if hotkey listener is active"""
        return self._is_running


def hotkey_string_to_pynput(hotkey: str) -> str:
    """Convert user-friendly hotkey string to pynput format."""
    hotkey = hotkey.lower().strip()
    
    replacements = {
        'command': 'cmd',
        'control': 'ctrl',
        'option': 'alt',
    }
    
    for old, new in replacements.items():
        hotkey = hotkey.replace(old, new)
    
    parts = [p.strip() for p in hotkey.split('+')]
    formatted = []
    
    for part in parts:
        if part in ('cmd', 'ctrl', 'alt', 'shift'):
            formatted.append(f'<{part}>')
        else:
            formatted.append(part)
    
    return '+'.join(formatted)


def pynput_to_display(hotkey: str) -> str:
    """Convert pynput hotkey string to display format"""
    manager = HotkeyManager(lambda: None, hotkey)
    return manager.get_display_string()
