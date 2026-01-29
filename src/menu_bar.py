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
    
    # Animation settings
    ANIMATION_FRAMES = 4
    ANIMATION_INTERVAL = 0.15  # seconds between frames
    
    def __init__(
        self,
        on_toggle: Optional[Callable[[], None]] = None,
        on_settings: Optional[Callable[[], None]] = None,
        on_history_select: Optional[Callable[[int], None]] = None,
        on_change_hotkey: Optional[Callable[[], None]] = None,
        on_quit: Optional[Callable[[], None]] = None,
        on_tick: Optional[Callable[[rumps.Timer], None]] = None
    ):
        """
        Initialize Menu Bar app.
        
        Args:
            on_toggle: Callback for start/stop recording
            on_settings: Callback for opening settings
            on_history_select: Callback when history item selected
            on_change_hotkey: Callback for changing hotkey
            on_quit: Callback before quitting
            on_tick: Callback called periodically (e.g. every 0.5s)
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
        self._on_tick = on_tick
        
        self._hotkey_display = "⌘⇧D"
        
        # Build menu
        self._build_menu()
        
    # @rumps.timer(0.5)
    def _on_tick_callback(self, sender):
        """Internal timer callback"""
        if self._on_tick:
            self._on_tick(sender)
    
    def _get_icon_path(self, status: str, frame: int = 0) -> Optional[str]:
        """Get icon path for status"""
        import sys
        import os
        
        # Handle PyInstaller path
        if hasattr(sys, '_MEIPASS'):
            app_dir = Path(sys._MEIPASS)
        else:
            app_dir = Path(__file__).parent.parent
        
        # For recording, return animation frame
        if status == "recording":
            frame_path = app_dir / "assets" / f"menu_icon_recording_{frame}.png"
            if frame_path.exists():
                return str(frame_path)
            
        icons = {
            "idle": app_dir / "assets" / "menu_icon_idle.png",
            "recording": app_dir / "assets" / "menu_icon_recording_0.png",
            "processing": app_dir / "assets" / "menu_icon_ready.png",
        }
        
        icon_path = icons.get(status, icons["idle"])
        if icon_path.exists():
            return str(icon_path)
        
        print(f"Warning: Icon not found at {icon_path}")
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
        

        
        # Quit
        quit_item = rumps.MenuItem("Quit MWhisper", callback=self._on_quit_click)
        
        # Version info (for debugging)
        # Version info (for debugging)
        version_item = rumps.MenuItem("Build: v25-custom-actions")
        version_item.set_callback(None)
        
        # Build menu
        self.menu = [
            self._toggle_item,
            None,  # Separator
            self._status_item,
            None,  # Separator
            self._history_menu,
            self._settings_item,

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
    on_quit: Optional[Callable[[], None]] = None,
    on_tick: Optional[Callable[[rumps.Timer], None]] = None
) -> MenuBarApp:
    """
    Create and return a MenuBarApp instance.
    
    Args:
        on_toggle: Callback for start/stop
        on_settings: Callback for settings
        on_history_select: Callback for history selection
        on_change_hotkey: Callback for changing hotkey
        on_quit: Callback before quit
        on_tick: Periodic callback
    
    Returns:
        MenuBarApp instance
    """
    return MenuBarApp(
        on_toggle=on_toggle,
        on_settings=on_settings,
        on_history_select=on_history_select,
        on_change_hotkey=on_change_hotkey,
        on_quit=on_quit,
        on_tick=on_tick
    )


# Test the menu bar
if __name__ == "__main__":
    def toggle():
        print("Toggle recording!")
    
    app = create_menu_bar_app(on_toggle=toggle)
    app.run()
