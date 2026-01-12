"""
MWhisper Text Inserter
Inserts text into the active application on macOS
"""

import subprocess
import time
from typing import Optional


class TextInserter:
    """Handles text insertion into active window on macOS"""
    
    def __init__(self, method: str = "clipboard"):
        """
        Initialize text inserter.
        
        Args:
            method: Insertion method - "keystroke" or "clipboard" (default: clipboard for Unicode support)
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
        # print("=== V10: insert() called ===")
        if not text:
            return True
        
        try:
            # Use Quartz method (robust, doesn't steal focus like osascript)
            return self._insert_via_clipboard(text)
        except Exception as e:
            print(f"Text insertion error: {e}")
            import traceback
            traceback.print_exc()
            # Fallback to AppleScript
            return self._insert_via_applescript(text)
    
    def _insert_via_keystroke(self, text: str) -> bool:
        """Insert text by simulating keystrokes"""
        # Escape special characters for AppleScript
        escaped_text = text.replace('\\', '\\\\').replace('"', '\\"')
        
        script = f'''
        tell application "System Events"
            keystroke "{escaped_text}"
        end tell
        '''
        
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"AppleScript error: {result.stderr}")
            return False
        
        return True
    
    def _insert_via_accessibility(self, text: str) -> bool:
        """Insert text using Accessibility API (bypasses keyboard layout)"""
        try:
            import ApplicationServices
            from ApplicationServices import (
                AXUIElementCreateSystemWide, 
                AXUIElementCopyAttributeValue, 
                AXUIElementSetAttributeValue,
                kAXFocusedUIElementAttribute, 
                kAXSelectedTextAttribute,
                kAXValueSuccess
            )

            system_wide = AXUIElementCreateSystemWide()
            error, focused_element = AXUIElementCopyAttributeValue(
                system_wide, kAXFocusedUIElementAttribute, None
            )

            if error != kAXValueSuccess or not focused_element:
                print("DEBUG: Could not get focused element")
                return False

            # Try to set valid text directly
            error = AXUIElementSetAttributeValue(
                focused_element, kAXSelectedTextAttribute, text
            )

            if error == kAXValueSuccess:
                print("DEBUG: Accessibility insertion successful")
                return True
            else:
                print(f"DEBUG: Accessibility insertion failed with error: {error}")
                return False

        except ImportError:
            print("DEBUG: ApplicationServices module not found (pyobjc framework issue?)")
            return False
        except Exception as e:
            print(f"DEBUG: Accessibility insertion exception: {e}")
            return False

    def insert_text(self, text: str) -> bool:
        """Insert text into the active application"""
        print("=== V9_MARKER: insert_text called ===")  # UNIQUE MARKER
        if not text:
            return False
            
        print(f"Inserting: {text}")

        # Use pure AppleScript - it handles Unicode natively
        if self._insert_via_applescript(text):
            print("✓ Text inserted successfully")
            return True
        
        return False
    
    def _insert_via_applescript(self, text: str) -> bool:
        """Insert text using pbcopy + AppleScript keystroke"""
        print("=== V9_MARKER: _insert_via_applescript called ===")  # UNIQUE MARKER
        try:
            import subprocess
            import time
            import os
            
            print(f"[STEP 1] Starting insertion for: {text[:30]}...")
            
            # Step 1: Use pbcopy to set clipboard
            print("[STEP 2] Calling pbcopy...")
            env = os.environ.copy()
            env['LANG'] = 'en_US.UTF-8'
            
            # Use full path to pbcopy
            pbcopy_path = '/usr/bin/pbcopy'
            print(f"[STEP 3] pbcopy path: {pbcopy_path}")
            
            process = subprocess.Popen(
                [pbcopy_path],
                stdin=subprocess.PIPE,
                env=env
            )
            stdout, stderr = process.communicate(text.encode('utf-8'))
            exit_code = process.wait()
            
            print(f"[STEP 4] pbcopy exit code: {exit_code}")
            if exit_code != 0:
                print(f"[ERROR] pbcopy failed with exit code {exit_code}")
                return False
            
            # Step 2: Verify clipboard was set
            print("[STEP 5] Verifying clipboard with pbpaste...")
            verify = subprocess.run(['/usr/bin/pbpaste'], capture_output=True, text=True, env=env)
            print(f"[STEP 6] pbpaste result: '{verify.stdout[:50]}...'")
            
            if verify.stdout.strip() != text.strip():
                print(f"[WARNING] Clipboard mismatch!")
                print(f"[WARNING] Expected: '{text[:30]}...'")
                print(f"[WARNING] Got: '{verify.stdout[:30]}...'")
            
            # Step 3: Wait for clipboard to be ready
            print("[STEP 7] Waiting 200ms...")
            time.sleep(0.2)
            
            # Step 4: Use AppleScript for keystroke
            print("[STEP 8] Calling osascript for Cmd+V...")
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
            
            print(f"[STEP 9] osascript exit code: {result.returncode}")
            if result.returncode != 0:
                print(f"[ERROR] osascript failed: {result.stderr}")
                return False
            
            print("[STEP 10] Insertion complete!")
            return True
            
        except Exception as e:
            print(f"[EXCEPTION] Insertion failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _insert_via_clipboard(self, text: str) -> bool:
        """Insert text via clipboard and paste using native Cocoa + Quartz events"""
        try:
            import time
            import subprocess
            from AppKit import NSPasteboard, NSPasteboardTypeString
            from Foundation import NSData
            import Quartz
            
            # Get pasteboard
            pasteboard = NSPasteboard.generalPasteboard()
            
            # Save current clipboard content
            old_clipboard = None
            try:
                old_clipboard = pasteboard.stringForType_(NSPasteboardTypeString)
            except:
                pass
            
            # CRITICAL: Clear and set data as UTF-8 bytes
            pasteboard.clearContents()
            
            # Convert text to UTF-8 NSData and set using declareTypes/setData
            utf8_data = text.encode('utf-8')
            ns_data = NSData.dataWithBytes_length_(utf8_data, len(utf8_data))
            
            # Declare both string and UTF-8 types
            pasteboard.declareTypes_owner_([NSPasteboardTypeString, 'public.utf8-plain-text'], None)
            pasteboard.setData_forType_(ns_data, 'public.utf8-plain-text')
            pasteboard.setString_forType_(text, NSPasteboardTypeString)
            
            print(f"DEBUG: Set clipboard to: {text[:50]}...")
            
            # Longer delay to ensure clipboard is updated
            time.sleep(0.2)
            
            # Use Quartz to simulate Cmd+V (Physical Key Code 9)
            # This is more robust than AppleScript
            print("DEBUG: Simulating Cmd+V via Quartz...")
            
            # Cmd down
            cmd_down = Quartz.CGEventCreateKeyboardEvent(None, 0x37, True) # kVK_Command
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, cmd_down)
            
            # V down (keycode 0x09)
            v_down = Quartz.CGEventCreateKeyboardEvent(None, 0x09, True) # kVK_ANSI_V
            Quartz.CGEventSetFlags(v_down, Quartz.kCGEventFlagMaskCommand)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, v_down)
            
            # V up
            v_up = Quartz.CGEventCreateKeyboardEvent(None, 0x09, False)
            Quartz.CGEventSetFlags(v_up, Quartz.kCGEventFlagMaskCommand)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, v_up)
            
            # Cmd up
            cmd_up = Quartz.CGEventCreateKeyboardEvent(None, 0x37, False)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, cmd_up)
            
            # Delay before restoring clipboard
            time.sleep(0.3)
            
            # Restore clipboard after paste
            if old_clipboard is not None:
                try:
                    pasteboard.clearContents()
                    pasteboard.setString_forType_(old_clipboard, NSPasteboardTypeString)
                except:
                    pass
            
            return True
            
        except Exception as e:
            print(f"Clipboard insertion error: {e}")
            import traceback
            traceback.print_exc()
            return False
    def set_method(self, method: str) -> None:
        """Set the insertion method"""
        if method in ("keystroke", "clipboard"):
            self.method = method
    
    @staticmethod
    def get_active_app() -> Optional[str]:
        """Get the name of the currently active application"""
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
        return None
    
    @staticmethod
    def check_accessibility() -> bool:
        """Check if accessibility permission is granted"""
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


def insert_text(text: str, method: str = "clipboard") -> bool:
    """
    Convenience function to insert text.
    
    Args:
        text: Text to insert
        method: "keystroke" or "clipboard" (default: clipboard for Unicode)
    
    Returns:
        True if successful
    """
    inserter = TextInserter(method)
    return inserter.insert(text)


# Test the module
if __name__ == "__main__":
    print("Text Inserter Test")
    print("-" * 30)
    
    # Check accessibility
    if TextInserter.check_accessibility():
        print("✓ Accessibility permission granted")
    else:
        print("✗ Accessibility permission required!")
        print("Go to: System Preferences → Security & Privacy → Privacy → Accessibility")
    
    # Show active app
    active_app = TextInserter.get_active_app()
    print(f"Active app: {active_app}")
    
    # Test insertion (uncomment to test)
    # print("\nInserting text in 3 seconds...")
    # time.sleep(3)
    # insert_text("Hello from MWhisper!")
