"""
MWhisper Hotkey Manager
Push-to-talk global hotkeys for macOS using pynput
"""

from pynput import keyboard
from typing import Callable, Optional, Set
import threading
import subprocess


# Virtual Key Code Map for macOS (QWERTY Physical -> VK Code)
VK_MAP = {
    'a': 0, 's': 1, 'd': 2, 'f': 3, 'h': 4, 'g': 5, 'z': 6, 'x': 7, 'c': 8, 'v': 9,
    'b': 11, 'q': 12, 'w': 13, 'e': 14, 'r': 15, 'y': 16, 't': 17, '1': 18, '2': 19,
    '3': 20, '4': 21, '6': 22, '5': 23, '=': 24, '9': 25, '7': 26, '-': 27, '8': 28,
    '0': 29, ']': 30, 'o': 31, 'u': 32, '[': 33, 'i': 34, 'p': 35, 'l': 37, 'j': 38,
    "'": 39, 'k': 40, ';': 41, '\\': 42, ',': 43, '/': 44, 'n': 45, 'm': 46, '.': 47,
    '`': 50, 'space': 49, '±': 10, '§': 10
}

# Layout mapping for normalization (Fallback)
LAYOUT_MAP = {
    'й': 'q', 'ц': 'w', 'у': 'e', 'к': 'r', 'е': 't', 'н': 'y', 'г': 'u', 'ш': 'i', 'щ': 'o', 'з': 'p', 'х': '[', 'ъ': ']',
    'ф': 'a', 'ы': 's', 'в': 'd', 'а': 'f', 'п': 'g', 'р': 'h', 'о': 'j', 'л': 'k', 'д': 'l', 'ж': ';', 'э': "'",
    'я': 'z', 'ч': 'x', 'с': 'c', 'м': 'v', 'и': 'b', 'т': 'n', 'ь': 'm', 'б': ',', 'ю': '.', 'ё': '`',
    'і': 's', 'ї': ']', 'є': "'", 'ґ': '\\'
}

# Reverse mapping for robust key name resolution (VK -> QWERTY char)
VK_TO_CHAR = {v: k for k, v in VK_MAP.items()}

def get_safe_key_name(key) -> Optional[str]:
    """
    Get normalized key name using robust strategy (VK -> Char -> Name).
    This function is CRASH-PROOF for Ukrainian/International layouts.
    """
    # 1. Check valid VK (Physical) - Primary Source of Truth
    if hasattr(key, 'vk') and key.vk in VK_TO_CHAR:
        return VK_TO_CHAR[key.vk]
        
    # 2. Check explicitly handled modifiers/specials (pynput standard names)
    if hasattr(key, 'name'):
        name = key.name.lower()
        if name.endswith('_r') or name.endswith('_l'):
             name = name[:-2]
        return name
        
    # 3. Fallback to char (Risky on some layouts, so wrap in try/except)
    try:
        if hasattr(key, 'char') and key.char:
            char = key.char.lower()
            # Normalize via LAYOUT_MAP just in case we ended up here
            if char in LAYOUT_MAP:
                return LAYOUT_MAP[char]
            return char
    except Exception:
        # If getting char crashes (pynput issue with certain layouts), return None
        pass
        
    return None


class MasterHotkeyListener:
    """
    Singleton listener that dispatches key events to registered hotkey handlers.
    This prevents creating multiple pynput Listeners which causes crashes on macOS.
    """
    _instance = None
    _lock = threading.Lock()
    _listener = None
    _handlers = set()
    _is_running = False

    @classmethod
    def get_instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def register(self, handler):
        with self._lock:
            self._handlers.add(handler)
            if not self._is_running:
                self._start()

    def unregister(self, handler):
        with self._lock:
            self._handlers.discard(handler)
            # We intentionally do NOT stop the listener when handlers are empty
            # to avoid issues with restarting pynput listener on macOS.
            # It will stop only when the app exits.

    def _start(self):
        try:
            self._listener = keyboard.Listener(
                on_press=self._on_key_press,
                on_release=self._on_key_release
            )
            self._listener.start()
            self._is_running = True
            print("⌨️  Master Hotkey Listener started")
        except Exception as e:
            print(f"Failed to start master listener: {e}")
            raise

    def _stop(self):
        if self._listener:
            try:
                self._listener.stop()
            except:
                pass
            self._listener = None
        self._is_running = False
        print("⌨️  Master Hotkey Listener stopped")

    def _on_key_press(self, key):
        # Dispatch to all handlers
        # We need a copy because handlers might modify the set during callback (unlikely but safe)
        for handler in list(self._handlers):
            try:
                handler._on_key_press(key)
            except Exception as e:
                print(f"Error in hotkey handler press: {e}")

    def _on_key_release(self, key):
        for handler in list(self._handlers):
            try:
                handler._on_key_release(key)
            except Exception as e:
                print(f"Error in hotkey handler release: {e}")


class PushToTalkHotkey:
    """
    Push-to-talk hotkey manager.
    Uses MasterHotkeyListener to share a single keyboard hook.
    """
    
    # Key name mappings for display
    KEY_DISPLAY_NAMES = {
        'cmd': '⌘',
        'ctrl': '⌃',
        'alt': '⌥',
        'shift': '⇧',
        'space': 'Space',
    }
    
    # Expose maps via class used by instances, but they refer to module globals now
    VK_MAP = VK_MAP
    LAYOUT_MAP = LAYOUT_MAP
    VK_TO_CHAR = VK_TO_CHAR

    def __init__(
        self,
        hotkey: str,
        on_press: Callable[[], None],
        on_release: Callable[[], None]
    ):
        self.hotkey_string = hotkey
        self.on_press_callback = on_press
        self.on_release_callback = on_release
        
        # Parse hotkey
        self._required_modifiers, self._main_key = self._parse_hotkey(hotkey)
        
        # Resolve Main Key VK
        self._main_key_vk = None
        if self._main_key and self._main_key in self.VK_MAP:
            self._main_key_vk = self.VK_MAP[self._main_key]
        
        # State
        self._is_pressed = False
        self._current_modifiers: Set[str] = set()
        self._lock = threading.Lock()
        self._registered = False
    
    def _parse_hotkey(self, hotkey: str) -> tuple:
        """Parse hotkey string into modifiers and main key"""
        parts = hotkey.lower().replace('<', '').replace('>', '').replace('command', 'cmd').replace('control', 'ctrl').split('+')
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
        """Delegate to global safe resolver"""
        return get_safe_key_name(key)
    
    def _check_modifiers(self) -> bool:
        """Check if all required modifiers are currently pressed"""
        return self._required_modifiers.issubset(self._current_modifiers)
    
    def _matches_main_key(self, key, key_name) -> bool:
        """Check if key matches configured main key (using robust multi-strategy)"""
        
        # Strategy 1: Check Virtual Key Code (Physical Position)
        if self._main_key_vk is not None and hasattr(key, 'vk') and key.vk is not None:
             if key.vk == self._main_key_vk:
                 return True
        
        # Strategy 2: Check Actual Character (Safe Access) - Fix for ISO Backtick/Section mismatch
        try:
            if hasattr(key, 'char') and key.char:
                char = key.char.lower()
                if char == self._main_key:
                    return True
                if char in self.LAYOUT_MAP and self.LAYOUT_MAP[char] == self._main_key:
                    return True
        except Exception:
            pass
            
        # Strategy 3: Check Resolved Key Name (Fallback)
        if key_name and key_name == self._main_key:
            return True
            
        return False
    
    def _on_key_press(self, key) -> None:
        """Handle key press event from master listener"""
        # 1. Modifiers
        is_modifier = False
        key_name = None
        
        if hasattr(key, 'name'):
            name = key.name
            if name in ('cmd', 'ctrl', 'alt', 'shift', 'cmd_r', 'ctrl_r', 'alt_r', 'shift_r'):
                is_modifier = True
                key_name = name.replace('_r', '').replace('_l', '')
        
        if is_modifier and key_name:
            self._current_modifiers.add(key_name)
            return

        # 2. Key Check (Robust Match)
        safe_name = get_safe_key_name(key)
            
        if self._matches_main_key(key, safe_name) and self._check_modifiers():
             self._trigger_press()

    def _trigger_press(self):
        with self._lock:
            # Debounce
            if not self._is_pressed:
                self._is_pressed = True
                print(f"🔥 HOTKEY PRESSED: {self.hotkey_string}")
                try:
                    self.on_press_callback()
                except Exception as e:
                    print(f"Hotkey press callback error: {e}")

    def _on_key_release(self, key) -> None:
        """Handle key release event from master listener"""
        is_modifier = False
        key_name = None
        if hasattr(key, 'name'):
            name = key.name
            if name in ('cmd', 'ctrl', 'alt', 'shift', 'cmd_r', 'ctrl_r', 'alt_r', 'shift_r'):
                is_modifier = True
                key_name = name.replace('_r', '').replace('_l', '')
                
        if is_modifier and key_name:
            self._current_modifiers.discard(key_name)
            
        should_release = False
        
        # Resolve Safe
        safe_name = get_safe_key_name(key)
        
        if self._matches_main_key(key, safe_name):
             should_release = True
             
        if not self._check_modifiers():
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
        """Register with master listener"""
        if not self._registered:
            MasterHotkeyListener.get_instance().register(self)
            self._registered = True
            print(f"⌨️  Push-to-talk hotkey active: {self.get_display_string()} (VK: {self._main_key_vk})")
    
    def stop(self) -> None:
        """Unregister from master listener"""
        if self._registered:
            MasterHotkeyListener.get_instance().unregister(self)
            self._registered = False
            self._is_pressed = False
            self._current_modifiers.clear()
    
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
        return self._registered


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
        self._ptt = PushToTalkHotkey(
            hotkey=self.hotkey_string,
            on_press=lambda: None,  # No action on press
            on_release=self.callback
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
        """Capture a new hotkey combination from user input (SAFE & ROBUST)"""
        import time
        
        captured_modifiers: Set[str] = set()
        main_key: Optional[str] = None
        capture_done = threading.Event()
        
        def on_press(key):
            nonlocal main_key, captured_modifiers
            
            try:
                # 1. Modifiers
                if hasattr(key, 'name'):
                    key_name = key.name
                    if key_name in ('cmd', 'ctrl', 'alt', 'shift', 'cmd_r', 'ctrl_r', 'alt_r', 'shift_r'):
                        mod = key_name.replace('_r', '').replace('_l', '')
                        captured_modifiers.add(mod)
                        return
                
                # 2. Main Key using SAFE Resolver
                safe_name = get_safe_key_name(key)
                
                if safe_name:
                    main_key = safe_name
                    if captured_modifiers:
                        capture_done.set()
                        return False # Stop listener
                        
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
