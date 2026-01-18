from pynput import keyboard
import sys

print("=== Keyboard Event Debugger ===")
print("Press any key to see its details.")
print("Press ESC to exit.")
print("===============================")

# Virtual Key Code Map for macOS (QWERTY Physical -> VK Code)
# Copied from src/hotkeys.py for standalone testing
VK_MAP = {
    'a': 0, 's': 1, 'd': 2, 'f': 3, 'h': 4, 'g': 5, 'z': 6, 'x': 7, 'c': 8, 'v': 9,
    'b': 11, 'q': 12, 'w': 13, 'e': 14, 'r': 15, 'y': 16, 't': 17, '1': 18, '2': 19,
    '3': 20, '4': 21, '6': 22, '5': 23, '=': 24, '9': 25, '7': 26, '-': 27, '8': 28,
    '0': 29, ']': 30, 'o': 31, 'u': 32, '[': 33, 'i': 34, 'p': 35, 'l': 37, 'j': 38,
    "'": 39, 'k': 40, ';': 41, '\\': 42, ',': 43, '/': 44, 'n': 45, 'm': 46, '.': 47,
    '`': 50, 'space': 49, '§': 10, '±': 10
}
VK_TO_CHAR = {v: k for k, v in VK_MAP.items()}

import signal
import sys

def signal_handler(sig, frame):
    print("\n[!] SIGQUIT received (Ctrl+\\). Note: This is a system shortcut, NOT a crash!")
    # We continue running to confirm stability
    
signal.signal(signal.SIGQUIT, signal_handler)

def on_press(key):
    try:
        # 1. Try Safe VK access first (Crash Proof)
        vk_code = getattr(key, 'vk', None)
        
        safe_name = "UNK"
        if vk_code is not None and vk_code in VK_TO_CHAR:
            safe_name = f"Safe resolved: '{VK_TO_CHAR[vk_code]}' (VK {vk_code})"
            
        print(f"Key Event Detected (VK: {vk_code})")
        print(f"   -> {safe_name}")
        
        # 2. Only try char if we really need to (and catch crash if possible in python)
        if vk_code is None:
            try:
                char = getattr(key, 'char', 'N/A')
                print(f"   -> Fallback Char: {char!r}")
            except:
                print("   -> Fallback Char: <CRASH PREVENTED>")
            
    except Exception as e:
        print(f"Error handling key: {e}")

def on_release(key):
    # Don't print key here either
    if key == keyboard.Key.esc:
        print("Exiting...")
        return False

# Collect events until released
with keyboard.Listener(
        on_press=on_press,
        on_release=on_release) as listener:
    listener.join()
