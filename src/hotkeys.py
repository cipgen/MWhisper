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
                
            except Exception as e:
                print(f"Failed to start hotkey listener: {e}")
                print("\n⚠️  Hotkeys require Input Monitoring permission!")
                print("Add MWhisper to: System Settings → Privacy & Security → Input Monitoring")
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
    
    def capture_hotkey(self, callback: Callable[[str, str], None], timeout: float = 10.0) -> None:
        """
        Capture a new hotkey combination from user input.
        
        Args:
            callback: Called with (pynput_format, display_format) when hotkey captured
            timeout: Seconds to wait before giving up
        """
        import time
        
        captured_modifiers: Set[str] = set()
        main_key: Optional[str] = None
        capture_done = threading.Event()
        
        def on_press(key):
            nonlocal main_key, captured_modifiers
            
            try:
                # Check for modifier keys
                if hasattr(key, 'name'):
                    key_name = key.name
                    if key_name in ('cmd', 'ctrl', 'alt', 'shift', 'cmd_r', 'ctrl_r', 'alt_r', 'shift_r'):
                        # Normalize right modifiers to left
                        mod = key_name.replace('_r', '').replace('_l', '')
                        captured_modifiers.add(mod)
                        return  # Continue listening
                
                # Regular key pressed
                if hasattr(key, 'char') and key.char:
                    main_key = key.char.lower()
                elif hasattr(key, 'name'):
                    main_key = key.name.lower()
                
                if main_key and captured_modifiers:
                    capture_done.set()
                    return False  # Stop listener
                    
            except Exception as e:
                print(f"Key capture error: {e}")
        
        def on_release(key):
            pass
        
        # Start temporary listener
        temp_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        temp_listener.start()
        
        # Wait for capture or timeout
        def wait_for_capture():
            start = time.time()
            while time.time() - start < timeout:
                if capture_done.wait(0.1):
                    break
            
            temp_listener.stop()
            
            if main_key and captured_modifiers:
                # Build pynput format string
                parts = [f'<{mod}>' for mod in sorted(captured_modifiers)]
                parts.append(main_key)
                pynput_format = '+'.join(parts)
                
                # Build display string
                display_parts = []
                for mod in sorted(captured_modifiers):
                    display_parts.append(self.KEY_DISPLAY_NAMES.get(mod, mod.upper()))
                display_parts.append(main_key.upper())
                display_format = ''.join(display_parts)
                
                callback(pynput_format, display_format)
            else:
                callback(None, None)  # Timeout or cancelled
        
        threading.Thread(target=wait_for_capture, daemon=True).start()


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
