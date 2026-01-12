"""
MWhisper Menu Bar Application
macOS Menu Bar interface using rumps
"""

import rumps
from typing import Optional, Callable, List
from pathlib import Path


class MenuBarApp(rumps.App):
    """Menu Bar application for MWhisper"""
    
    # Status constants
    STATUS_IDLE = "idle"
    STATUS_RECORDING = "recording"
    STATUS_PROCESSING = "processing"
    
    def __init__(
        self,
        on_toggle: Optional[Callable[[], None]] = None,
        on_settings: Optional[Callable[[], None]] = None,
        on_history_select: Optional[Callable[[int], None]] = None,
        on_change_hotkey: Optional[Callable[[], None]] = None,
        on_quit: Optional[Callable[[], None]] = None
    ):
        """
        Initialize Menu Bar app.
        
        Args:
            on_toggle: Callback for start/stop recording
            on_settings: Callback for opening settings
            on_history_select: Callback when history item selected
            on_change_hotkey: Callback for changing hotkey
            on_quit: Callback before quitting
        """
        # Initialize with default icon
        super().__init__(
            name="MWhisper",
            icon=self._get_icon_path("idle"),
            quit_button=None  # We'll add custom quit
        )
        
        self._status = self.STATUS_IDLE
        self._on_toggle = on_toggle
        self._on_settings = on_settings
        self._on_history_select = on_history_select
        self._on_change_hotkey = on_change_hotkey
        self._on_quit = on_quit
        
        self._hotkey_display = "⌘⇧D"
        
        # Build menu
        self._build_menu()
    
    def _get_icon_path(self, status: str) -> Optional[str]:
        """Get icon path for status"""
        import sys
        import os
        
        # Handle PyInstaller path
        if hasattr(sys, '_MEIPASS'):
            app_dir = Path(sys._MEIPASS)
        else:
            app_dir = Path(__file__).parent.parent
            
        icons = {
            "idle": app_dir / "assets" / "icon_idle.png",
            "recording": app_dir / "assets" / "icon_active.png",
            "processing": app_dir / "assets" / "icon_ready.png",
        }
        
        icon_path = icons.get(status, icons["idle"])
        if icon_path.exists():
            return str(icon_path)
        
        print(f"Warning: Icon not found at {icon_path}")
        return None
        
        # Return None to use text-based icon
        return None
    
    def _build_menu(self) -> None:
        """Build the menu items"""
        # Toggle button updates dynamically
        self._toggle_item = rumps.MenuItem(
            f"Start Recording ({self._hotkey_display})",
            callback=self._on_toggle_click
        )
        
        # Status display (not clickable)
        self._status_item = rumps.MenuItem("Status: Ready")
        self._status_item.set_callback(None)
        
        # History submenu - add empty item initially
        self._history_menu = rumps.MenuItem("History")
        empty_item = rumps.MenuItem("No history")
        empty_item.set_callback(None)
        self._history_menu[empty_item.title] = empty_item
        
        # Settings
        self._settings_item = rumps.MenuItem(
            "Settings...",
            callback=self._on_settings_click
        )
        
        # Change Hotkey
        self._change_hotkey_item = rumps.MenuItem(
            "Change Hotkey...",
            callback=self._on_change_hotkey_click
        )
        
        # Quit
        quit_item = rumps.MenuItem("Quit MWhisper", callback=self._on_quit_click)
        
        # Version info (for debugging)
        version_item = rumps.MenuItem("Build: 2026-01-11-v13")
        version_item.set_callback(None)
        
        # Build menu
        self.menu = [
            self._toggle_item,
            None,  # Separator
            self._status_item,
            None,  # Separator
            self._history_menu,
            self._settings_item,
            self._change_hotkey_item,
            None,  # Separator
            version_item,
            quit_item
        ]
    
    def _on_toggle_click(self, sender: rumps.MenuItem) -> None:
        """Handle toggle button click"""
        if self._on_toggle:
            self._on_toggle()
    
    def _on_settings_click(self, sender: rumps.MenuItem) -> None:
        """Handle settings click"""
        if self._on_settings:
            self._on_settings()
        else:
            rumps.alert(
                title="Settings",
                message="Settings will be available in a future update.",
                ok="OK"
            )
    
    def _on_change_hotkey_click(self, sender: rumps.MenuItem) -> None:
        """Handle change hotkey click"""
        if self._on_change_hotkey:
            self._on_change_hotkey()
        else:
            rumps.alert(
                title="Change Hotkey",
                message="Press a new key combination when prompted.",
                ok="OK"
            )
    
    def _on_quit_click(self, sender: rumps.MenuItem) -> None:
        """Handle quit click"""
        if self._on_quit:
            self._on_quit()
        rumps.quit_application()
    
    def _on_history_item_click(self, sender: rumps.MenuItem) -> None:
        """Handle history item click"""
        if self._on_history_select and hasattr(sender, '_history_index'):
            self._on_history_select(sender._history_index)
    
    def set_status(self, status: str, message: str = "") -> None:
        """
        Update status display.
        
        Args:
            status: One of STATUS_IDLE, STATUS_RECORDING, STATUS_PROCESSING
            message: Optional status message
        """
        self._status = status
        
        # Update icon
        icon_path = self._get_icon_path(status)
        if icon_path:
            self.icon = icon_path
        else:
            # Use emoji as fallback
            icons = {
                self.STATUS_IDLE: "🎤",
                self.STATUS_RECORDING: "🔴",
                self.STATUS_PROCESSING: "⏳"
            }
            self.title = icons.get(status, "🎤")
        
        # Update toggle button text
        if status == self.STATUS_RECORDING:
            self._toggle_item.title = f"Stop Recording ({self._hotkey_display})"
        else:
            self._toggle_item.title = f"Start Recording ({self._hotkey_display})"
        
        # Update status text
        status_messages = {
            self.STATUS_IDLE: "Status: Ready",
            self.STATUS_RECORDING: "Status: Recording...",
            self.STATUS_PROCESSING: "Status: Processing..."
        }
        status_text = status_messages.get(status, "Status: Ready")
        if message:
            status_text = f"Status: {message}"
        self._status_item.title = status_text
    
    def update_history_menu(self, entries: List[str]) -> None:
        """
        Update history submenu.
        
        Args:
            entries: List of history entry preview strings
        """
        self._update_history_menu(entries)
    
    def _update_history_menu(self, entries: List[str]) -> None:
        """Internal method to update history menu"""
        # Clear existing items safely
        try:
            # Only clear if menu has been initialized
            if hasattr(self._history_menu, '_menu') and self._history_menu._menu is not None:
                self._history_menu.clear()
            else:
                # Menu not yet initialized, clear by keys
                for key in list(self._history_menu.keys()):
                    del self._history_menu[key]
        except Exception:
            pass
        
        if not entries:
            empty_item = rumps.MenuItem("No history")
            empty_item.set_callback(None)
            self._history_menu[empty_item.title] = empty_item
            return
        
        for i, entry in enumerate(entries[:10]):  # Show max 10
            item = rumps.MenuItem(entry, callback=self._on_history_item_click)
            item._history_index = i
            self._history_menu[entry] = item
    
    def set_hotkey_display(self, display: str) -> None:
        """Update hotkey display in menu"""
        self._hotkey_display = display
        self.set_status(self._status)  # Refresh toggle button
    
    def show_notification(self, title: str, message: str) -> None:
        """Show a notification"""
        rumps.notification(
            title=title,
            subtitle="",
            message=message
        )
    
    def show_alert(self, title: str, message: str) -> None:
        """Show an alert dialog"""
        rumps.alert(title=title, message=message)


def create_menu_bar_app(
    on_toggle: Optional[Callable[[], None]] = None,
    on_settings: Optional[Callable[[], None]] = None,
    on_history_select: Optional[Callable[[int], None]] = None,
    on_change_hotkey: Optional[Callable[[], None]] = None,
    on_quit: Optional[Callable[[], None]] = None
) -> MenuBarApp:
    """
    Create and return a MenuBarApp instance.
    
    Args:
        on_toggle: Callback for start/stop
        on_settings: Callback for settings
        on_history_select: Callback for history selection
        on_change_hotkey: Callback for changing hotkey
        on_quit: Callback before quit
    
    Returns:
        MenuBarApp instance
    """
    return MenuBarApp(
        on_toggle=on_toggle,
        on_settings=on_settings,
        on_history_select=on_history_select,
        on_change_hotkey=on_change_hotkey,
        on_quit=on_quit
    )


# Test the menu bar
if __name__ == "__main__":
    def toggle():
        print("Toggle recording!")
    
    app = create_menu_bar_app(on_toggle=toggle)
    app.run()
