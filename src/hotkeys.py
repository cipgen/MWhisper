"""
MWhisper Hotkey Manager
Push-to-talk global hotkeys for macOS using pynput
"""

from pynput import keyboard
from typing import Callable, Optional, Set
import threading
import subprocess


class PushToTalkHotkey:
    """
    Push-to-talk hotkey manager.
    Calls on_press when hotkey is pressed, on_release when released.
    """
    
    # Key name mappings for display
    KEY_DISPLAY_NAMES = {
        'cmd': '⌘',
        'ctrl': '⌃',
        'alt': '⌥',
        'shift': '⇧',
        'space': 'Space',
    }
    
    # Modifier key sets for detection
    MODIFIER_KEYS = {
        keyboard.Key.cmd, keyboard.Key.cmd_r,
        keyboard.Key.ctrl, keyboard.Key.ctrl_r,
        keyboard.Key.alt, keyboard.Key.alt_r,
        keyboard.Key.shift, keyboard.Key.shift_r,
    }
    
    def __init__(
        self,
        hotkey: str,
        on_press: Callable[[], None],
        on_release: Callable[[], None]
    ):
        """
        Initialize push-to-talk hotkey.
        
        Args:
            hotkey: Hotkey string (e.g., "<cmd>+<shift>+d")
            on_press: Called when hotkey is pressed
            on_release: Called when hotkey is released
        """
        self.hotkey_string = hotkey
        self.on_press_callback = on_press
        self.on_release_callback = on_release
        
        # Parse hotkey
        self._required_modifiers, self._main_key = self._parse_hotkey(hotkey)
        
        # State
        self._listener: Optional[keyboard.Listener] = None
        self._is_running = False
        self._is_pressed = False
        self._current_modifiers: Set[str] = set()
        self._lock = threading.Lock()
    
    def _parse_hotkey(self, hotkey: str) -> tuple:
        """Parse hotkey string into modifiers and main key"""
        parts = hotkey.lower().replace('<', '').replace('>', '').split('+')
        modifiers = set()
        main_key = None
        
        for part in parts:
            part = part.strip()
            if part in ('cmd', 'ctrl', 'alt', 'shift'):
                modifiers.add(part)
            else:
                main_key = part
        
        return modifiers, main_key
    
    def _get_key_name(self, key) -> Optional[str]:
        """Get normalized key name"""
        if hasattr(key, 'char') and key.char:
            return key.char.lower()
        elif hasattr(key, 'name'):
            name = key.name.lower()
            # Normalize left/right modifiers
            if name.endswith('_r') or name.endswith('_l'):
                name = name[:-2]
            return name
        return None
    
    def _check_modifiers(self) -> bool:
        """Check if all required modifiers are currently pressed"""
        return self._required_modifiers.issubset(self._current_modifiers)
    
    def _on_key_press(self, key) -> None:
        """Handle key press event"""
        key_name = self._get_key_name(key)
        if not key_name:
            return
        
        # Track modifier state
        if key_name in ('cmd', 'ctrl', 'alt', 'shift'):
            self._current_modifiers.add(key_name)
        
        # Check if hotkey combo is pressed
        if key_name == self._main_key and self._check_modifiers():
            with self._lock:
                if not self._is_pressed:
                    self._is_pressed = True
                    print(f"🔥 HOTKEY PRESSED: {self.hotkey_string}")
                    try:
                        self.on_press_callback()
                    except Exception as e:
                        print(f"Hotkey press callback error: {e}")
    
    def _on_key_release(self, key) -> None:
        """Handle key release event"""
        key_name = self._get_key_name(key)
        if not key_name:
            return
        
        # Track modifier state
        if key_name in ('cmd', 'ctrl', 'alt', 'shift'):
            self._current_modifiers.discard(key_name)
        
        # Check if main key or any required modifier was released
        should_release = False
        if key_name == self._main_key:
            should_release = True
        elif key_name in self._required_modifiers and not self._check_modifiers():
            should_release = True
        
        if should_release:
            with self._lock:
                if self._is_pressed:
                    self._is_pressed = False
                    print(f"🔥 HOTKEY RELEASED: {self.hotkey_string}")
                    try:
                        self.on_release_callback()
                    except Exception as e:
                        print(f"Hotkey release callback error: {e}")
    
    def start(self) -> None:
        """Start listening for hotkey"""
        with self._lock:
            if self._is_running:
                return
            
            try:
                self._listener = keyboard.Listener(
                    on_press=self._on_key_press,
                    on_release=self._on_key_release
                )
                self._listener.start()
                self._is_running = True
                print(f"⌨️  Push-to-talk hotkey started: {self.get_display_string()}")
                
            except Exception as e:
                print(f"Failed to start hotkey listener: {e}")
                print("\n⚠️  Hotkeys require Input Monitoring permission!")
                print("Add MWhisper to: System Settings → Privacy & Security → Input Monitoring")
                raise
    
    def stop(self) -> None:
        """Stop listening for hotkey"""
        with self._lock:
            if self._listener:
                self._listener.stop()
                self._listener = None
            self._is_running = False
            self._is_pressed = False
            self._current_modifiers.clear()
            print(f"⌨️  Push-to-talk hotkey stopped: {self.get_display_string()}")
    
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


# Legacy class for backwards compatibility (used in change_hotkey)
class HotkeyManager:
    """Legacy wrapper - now uses PushToTalkHotkey internally"""
    
    KEY_DISPLAY_NAMES = PushToTalkHotkey.KEY_DISPLAY_NAMES
    
    def __init__(
        self,
        callback: Callable[[], None],
        hotkey: str = "<cmd>+<shift>+d"
    ):
        self.callback = callback
        self.hotkey_string = hotkey
        self._ptt: Optional[PushToTalkHotkey] = None
        self._is_running = False
    
    def start(self) -> None:
        if self._is_running:
            return
        # For legacy mode, callback is only on release (like toggle but PTT)
        self._ptt = PushToTalkHotkey(
            hotkey=self.hotkey_string,
            on_press=lambda: None,  # No action on press
            on_release=self.callback  # Action on release
        )
        self._ptt.start()
        self._is_running = True
    
    def stop(self) -> None:
        if self._ptt:
            self._ptt.stop()
            self._ptt = None
        self._is_running = False
    
    def get_display_string(self) -> str:
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
        return self._is_running
    
    def set_hotkey(self, hotkey: str) -> None:
        was_running = self._is_running
        if was_running:
            self.stop()
        self.hotkey_string = hotkey
        if was_running:
            self.start()
    
    def capture_hotkey(self, callback: Callable[[str, str], None], timeout: float = 10.0) -> None:
        """Capture a new hotkey combination from user input"""
        import time
        
        captured_modifiers: Set[str] = set()
        main_key: Optional[str] = None
        capture_done = threading.Event()
        
        def on_press(key):
            nonlocal main_key, captured_modifiers
            
            try:
                if hasattr(key, 'name'):
                    key_name = key.name
                    if key_name in ('cmd', 'ctrl', 'alt', 'shift', 'cmd_r', 'ctrl_r', 'alt_r', 'shift_r'):
                        mod = key_name.replace('_r', '').replace('_l', '')
                        captured_modifiers.add(mod)
                        return
                
                if hasattr(key, 'char') and key.char:
                    main_key = key.char.lower()
                elif hasattr(key, 'name'):
                    main_key = key.name.lower()
                
                if main_key and captured_modifiers:
                    capture_done.set()
                    return False
                    
            except Exception as e:
                print(f"Key capture error: {e}")
        
        def on_release(key):
            pass
        
        temp_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        temp_listener.start()
        
        def wait_for_capture():
            start = time.time()
            while time.time() - start < timeout:
                if capture_done.wait(0.1):
                    break
            
            temp_listener.stop()
            
            if main_key and captured_modifiers:
                parts = [f'<{mod}>' for mod in sorted(captured_modifiers)]
                parts.append(main_key)
                pynput_format = '+'.join(parts)
                
                display_parts = []
                for mod in sorted(captured_modifiers):
                    display_parts.append(self.KEY_DISPLAY_NAMES.get(mod, mod.upper()))
                display_parts.append(main_key.upper())
                display_format = ''.join(display_parts)
                
                callback(pynput_format, display_format)
            else:
                callback(None, None)
        
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
