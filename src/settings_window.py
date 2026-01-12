"""
MWhisper Settings Window
Native macOS settings dialog using PyObjC
"""

import rumps
from typing import Optional, Callable
import subprocess


class SettingsWindow:
    """Simple settings dialog using rumps alerts"""
    
    def __init__(
        self,
        current_api_key: str = "",
        current_translate_hotkey: str = "<cmd>+<shift>+t",
        on_save: Optional[Callable[[str, str], None]] = None
    ):
        """
        Initialize settings window.
        
        Args:
            current_api_key: Current OpenAI API key
            current_translate_hotkey: Current translate hotkey
            on_save: Callback with (api_key, translate_hotkey) when saved
        """
        self.current_api_key = current_api_key
        self.current_translate_hotkey = current_translate_hotkey
        self.on_save = on_save
    
    def show(self) -> None:
        """Show settings dialog"""
        # Show API key input dialog
        self._show_api_key_dialog()
    
    def _show_api_key_dialog(self) -> None:
        """Show API key input dialog"""
        # Mask current key for display
        if self.current_api_key:
            masked = self.current_api_key[:10] + "..." + self.current_api_key[-4:]
        else:
            masked = "(not set)"
        
        # Use rumps window for text input
        window = rumps.Window(
            message=f"Current key: {masked}\n\nEnter new OpenAI API key (or leave empty to keep current):",
            title="OpenAI API Key",
            default_text="",
            ok="Save",
            cancel="Cancel",
            dimensions=(400, 24)
        )
        
        response = window.run()
        
        if response.clicked:
            new_key = response.text.strip()
            if new_key:
                self.current_api_key = new_key
            
            # Now show translate hotkey dialog
            self._show_hotkey_info()
    
    def _show_hotkey_info(self) -> None:
        """Show hotkey info dialog"""
        message = (
            f"Translate Hotkey: {self._format_hotkey(self.current_translate_hotkey)}\n\n"
            f"Use this hotkey to:\n"
            f"1. Record your voice\n"
            f"2. Transcribe speech\n"
            f"3. Send to OpenAI for translation\n"
            f"4. Insert translated text\n\n"
            f"To change hotkey, use 'Change Translate Hotkey...' in menu."
        )
        
        rumps.alert(
            title="Translation Settings",
            message=message,
            ok="OK"
        )
        
        # Call save callback
        if self.on_save:
            self.on_save(self.current_api_key, self.current_translate_hotkey)
    
    def _format_hotkey(self, hotkey: str) -> str:
        """Format hotkey for display"""
        mapping = {
            '<cmd>': '⌘',
            '<shift>': '⇧',
            '<ctrl>': '⌃',
            '<alt>': '⌥',
        }
        result = hotkey.lower()
        for key, symbol in mapping.items():
            result = result.replace(key, symbol)
        result = result.replace('+', '')
        return result.upper()


def show_settings_window(
    current_api_key: str = "",
    current_translate_hotkey: str = "<cmd>+<shift>+t",
    on_save: Optional[Callable[[str, str], None]] = None
) -> None:
    """
    Convenience function to show settings window.
    
    Args:
        current_api_key: Current API key
        current_translate_hotkey: Current translate hotkey
        on_save: Callback when settings saved
    """
    window = SettingsWindow(current_api_key, current_translate_hotkey, on_save)
    window.show()


# Test
if __name__ == "__main__":
    def on_save(api_key, hotkey):
        print(f"Saved: API key={api_key[:10]}..., hotkey={hotkey}")
    
    app = rumps.App("Test")
    show_settings_window(
        current_api_key="sk-test-key-12345",
        on_save=on_save
    )
