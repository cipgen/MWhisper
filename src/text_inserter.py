"""
MWhisper Text Inserter
Cross-platform text insertion into the active application
Uses Quartz/AppKit on macOS, pyautogui on Windows
"""

import time
from typing import Optional
from .platform import is_macos, is_windows


class TextInserter:
    """Handles text insertion into active window - cross-platform"""
    
    def __init__(self, method: str = "clipboard"):
        """
        Initialize text inserter.
        
        Args:
            method: Insertion method - "keystroke" or "clipboard"
        """
        self.method = method
    
    def insert(self, text: str) -> bool:
        """
        Insert text into the currently active application.
        
        Args:
            text: Text to insert
        
        Returns:
            True if successful, False otherwise
        """
        if not text:
            return True
        
        try:
            if is_macos():
                return self._insert_macos(text)
            elif is_windows():
                return self._insert_windows(text)
            else:
                # Linux fallback
                return self._insert_linux(text)
        except Exception as e:
            print(f"Text insertion error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _insert_macos(self, text: str) -> bool:
        """Insert text on macOS using Quartz"""
        try:
            from AppKit import NSPasteboard, NSPasteboardTypeString
            from Foundation import NSData
            import Quartz
            
            pasteboard = NSPasteboard.generalPasteboard()
            
            # Save current clipboard
            old_clipboard = None
            try:
                old_clipboard = pasteboard.stringForType_(NSPasteboardTypeString)
            except:
                pass
            
            # Set clipboard
            pasteboard.clearContents()
            utf8_data = text.encode('utf-8')
            ns_data = NSData.dataWithBytes_length_(utf8_data, len(utf8_data))
            pasteboard.declareTypes_owner_([NSPasteboardTypeString, 'public.utf8-plain-text'], None)
            pasteboard.setData_forType_(ns_data, 'public.utf8-plain-text')
            pasteboard.setString_forType_(text, NSPasteboardTypeString)
            
            time.sleep(0.2)
            
            # Cmd+V via Quartz
            cmd_down = Quartz.CGEventCreateKeyboardEvent(None, 0x37, True)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, cmd_down)
            
            v_down = Quartz.CGEventCreateKeyboardEvent(None, 0x09, True)
            Quartz.CGEventSetFlags(v_down, Quartz.kCGEventFlagMaskCommand)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, v_down)
            
            v_up = Quartz.CGEventCreateKeyboardEvent(None, 0x09, False)
            Quartz.CGEventSetFlags(v_up, Quartz.kCGEventFlagMaskCommand)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, v_up)
            
            cmd_up = Quartz.CGEventCreateKeyboardEvent(None, 0x37, False)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, cmd_up)
            
            time.sleep(0.3)
            
            # Restore clipboard
            if old_clipboard is not None:
                try:
                    pasteboard.clearContents()
                    pasteboard.setString_forType_(old_clipboard, NSPasteboardTypeString)
                except:
                    pass
            
            return True
            
        except Exception as e:
            print(f"macOS insertion error: {e}")
            # Fallback to AppleScript
            return self._insert_macos_applescript(text)
    
    def _insert_macos_applescript(self, text: str) -> bool:
        """Fallback: Insert text on macOS using AppleScript"""
        import subprocess
        import os
        
        try:
            env = os.environ.copy()
            env['LANG'] = 'en_US.UTF-8'
            
            process = subprocess.Popen(
                ['/usr/bin/pbcopy'],
                stdin=subprocess.PIPE,
                env=env
            )
            process.communicate(text.encode('utf-8'))
            
            time.sleep(0.2)
            
            script = '''
            tell application "System Events"
                keystroke "v" using command down
            end tell
            '''
            
            result = subprocess.run(
                ['/usr/bin/osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"AppleScript insertion error: {e}")
            return False
    
    def _insert_windows(self, text: str) -> bool:
        """Insert text on Windows using pyautogui"""
        try:
            import pyperclip
            import pyautogui
            
            # Save current clipboard
            old_clipboard = None
            try:
                old_clipboard = pyperclip.paste()
            except:
                pass
            
            # Set clipboard and paste
            pyperclip.copy(text)
            time.sleep(0.1)
            
            # Ctrl+V to paste
            pyautogui.hotkey('ctrl', 'v')
            
            time.sleep(0.2)
            
            # Restore clipboard
            if old_clipboard is not None:
                try:
                    pyperclip.copy(old_clipboard)
                except:
                    pass
            
            return True
            
        except ImportError as e:
            print(f"Windows insertion requires pyautogui and pyperclip: {e}")
            return False
        except Exception as e:
            print(f"Windows insertion error: {e}")
            return False
    
    def _insert_linux(self, text: str) -> bool:
        """Insert text on Linux using xdotool or pyautogui"""
        try:
            import pyperclip
            import pyautogui
            
            pyperclip.copy(text)
            time.sleep(0.1)
            pyautogui.hotkey('ctrl', 'v')
            
            return True
        except Exception as e:
            print(f"Linux insertion error: {e}")
            # Fallback to xdotool
            try:
                import subprocess
                subprocess.run(['xclip', '-selection', 'clipboard'], input=text.encode(), check=True)
                subprocess.run(['xdotool', 'key', 'ctrl+v'], check=True)
                return True
            except:
                return False
    
    def delete_backwards(self, count: int) -> bool:
        """
        Delete characters backwards (simulate pressing backspace).
        Used for streaming mode.
        
        Args:
            count: Number of characters to delete
            
        Returns:
            True if successful
        """
        if count <= 0:
            return True
        
        try:
            if is_macos():
                return self._delete_backwards_macos(count)
            else:
                return self._delete_backwards_windows(count)
        except Exception as e:
            print(f"Delete backwards error: {e}")
            return False
    
    def _delete_backwards_macos(self, count: int) -> bool:
        """Delete backwards on macOS using Quartz"""
        import Quartz
        
        for i in range(count):
            key_down = Quartz.CGEventCreateKeyboardEvent(None, 0x33, True)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, key_down)
            
            key_up = Quartz.CGEventCreateKeyboardEvent(None, 0x33, False)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, key_up)
            
            if i % 10 == 0 and i > 0:
                time.sleep(0.01)
        
        return True
    
    def _delete_backwards_windows(self, count: int) -> bool:
        """Delete backwards on Windows using pyautogui"""
        import pyautogui
        
        for i in range(count):
            pyautogui.press('backspace')
            if i % 10 == 0 and i > 0:
                time.sleep(0.01)
        
        return True
    
    def insert_fast(self, text: str) -> bool:
        """
        Fast text insertion for streaming mode.
        
        Args:
            text: Text to insert
            
        Returns:
            True if successful
        """
        if not text:
            return True
        
        try:
            if is_macos():
                return self._insert_fast_macos(text)
            else:
                return self._insert_fast_windows(text)
        except Exception as e:
            print(f"Fast insert error: {e}")
            return False
    
    def _insert_fast_macos(self, text: str) -> bool:
        """Fast insert on macOS"""
        try:
            import Quartz
            from AppKit import NSPasteboard, NSPasteboardTypeString
            
            pasteboard = NSPasteboard.generalPasteboard()
            pasteboard.clearContents()
            pasteboard.setString_forType_(text, NSPasteboardTypeString)
            
            time.sleep(0.05)
            
            cmd_down = Quartz.CGEventCreateKeyboardEvent(None, 0x37, True)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, cmd_down)
            
            v_down = Quartz.CGEventCreateKeyboardEvent(None, 0x09, True)
            Quartz.CGEventSetFlags(v_down, Quartz.kCGEventFlagMaskCommand)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, v_down)
            
            v_up = Quartz.CGEventCreateKeyboardEvent(None, 0x09, False)
            Quartz.CGEventSetFlags(v_up, Quartz.kCGEventFlagMaskCommand)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, v_up)
            
            cmd_up = Quartz.CGEventCreateKeyboardEvent(None, 0x37, False)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, cmd_up)
            
            time.sleep(0.05)
            
            return True
            
        except Exception as e:
            print(f"Fast insert error: {e}")
            return False
    
    def _insert_fast_windows(self, text: str) -> bool:
        """Fast insert on Windows"""
        try:
            import pyperclip
            import pyautogui
            
            pyperclip.copy(text)
            time.sleep(0.05)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.05)
            
            return True
        except Exception as e:
            print(f"Fast insert error: {e}")
            return False
    
    def set_method(self, method: str) -> None:
        """Set the insertion method"""
        if method in ("keystroke", "clipboard"):
            self.method = method
    
    @staticmethod
    def get_active_app() -> Optional[str]:
        """Get the name of the currently active application"""
        if is_macos():
            import subprocess
            script = '''
            tell application "System Events"
                return name of first application process whose frontmost is true
            end tell
            '''
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return result.stdout.strip()
        elif is_windows():
            try:
                import win32gui
                return win32gui.GetWindowText(win32gui.GetForegroundWindow())
            except:
                pass
        return None
    
    @staticmethod
    def check_accessibility() -> bool:
        """Check if we have required permissions"""
        if is_macos():
            import subprocess
            script = '''
            tell application "System Events"
                return true
            end tell
            '''
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        else:
            # Windows doesn't require special permissions for this
            return True


def insert_text(text: str, method: str = "clipboard") -> bool:
    """
    Convenience function to insert text.
    
    Args:
        text: Text to insert
        method: "keystroke" or "clipboard"
    
    Returns:
        True if successful
    """
    inserter = TextInserter(method)
    return inserter.insert(text)


if __name__ == "__main__":
    print("Text Inserter Test")
    print("-" * 30)
    
    if TextInserter.check_accessibility():
        print("✓ Permissions OK")
    else:
        print("✗ Permissions required!")
    
    active_app = TextInserter.get_active_app()
    print(f"Active app: {active_app}")
