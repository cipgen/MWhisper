"""
MWhisper Menu Bar Application
Cross-platform system tray interface
Uses rumps on macOS, pystray on Windows
"""

from typing import Optional, Callable, List
from pathlib import Path
from .platform import is_macos, is_windows, is_linux


# Status constants (shared across platforms)
STATUS_IDLE = "idle"
STATUS_RECORDING = "recording"
STATUS_PROCESSING = "processing"


if is_macos():
    # macOS implementation using rumps
    import rumps
    
    class MenuBarApp(rumps.App):
        """Menu Bar application for MWhisper (macOS)"""
        
        STATUS_IDLE = STATUS_IDLE
        STATUS_RECORDING = STATUS_RECORDING
        STATUS_PROCESSING = STATUS_PROCESSING
        
        ANIMATION_FRAMES = 4
        ANIMATION_INTERVAL = 0.15
        
        def __init__(
            self,
            on_toggle: Optional[Callable[[], None]] = None,
            on_settings: Optional[Callable[[], None]] = None,
            on_history_select: Optional[Callable[[int], None]] = None,
            on_change_hotkey: Optional[Callable[[], None]] = None,
            on_quit: Optional[Callable[[], None]] = None,
            on_tick: Optional[Callable, None] = None
        ):
            super().__init__(
                name="MWhisper",
                icon=self._get_icon_path("idle"),
                quit_button=None
            )
            
            self._status = self.STATUS_IDLE
            self._on_toggle = on_toggle
            self._on_settings = on_settings
            self._on_history_select = on_history_select
            self._on_change_hotkey = on_change_hotkey
            self._on_quit = on_quit
            self._on_tick = on_tick
            
            self._hotkey_display = "⌘⇧D"
            self._build_menu()
            
        @rumps.timer(0.5)
        def _on_tick_callback(self, sender):
            if self._on_tick:
                self._on_tick(sender)
        
        def _get_icon_path(self, status: str, frame: int = 0) -> Optional[str]:
            import sys
            import os
            
            if hasattr(sys, '_MEIPASS'):
                app_dir = Path(sys._MEIPASS)
            else:
                app_dir = Path(__file__).parent.parent
            
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
            
            return None
        
        def _build_menu(self) -> None:
            self._toggle_item = rumps.MenuItem(
                f"Start Recording ({self._hotkey_display})",
                callback=self._on_toggle_click
            )
            
            self._status_item = rumps.MenuItem("Status: Ready")
            self._status_item.set_callback(None)
            
            self._history_menu = rumps.MenuItem("History")
            empty_item = rumps.MenuItem("No history")
            empty_item.set_callback(None)
            self._history_menu[empty_item.title] = empty_item
            
            self._settings_item = rumps.MenuItem(
                "Settings...",
                callback=self._on_settings_click
            )
            
            quit_item = rumps.MenuItem("Quit MWhisper", callback=self._on_quit_click)
            
            version_item = rumps.MenuItem("Build: v26-crossplatform")
            version_item.set_callback(None)
            
            self.menu = [
                self._toggle_item,
                None,
                self._status_item,
                None,
                self._history_menu,
                self._settings_item,
                None,
                version_item,
                quit_item
            ]
        
        def _on_toggle_click(self, sender) -> None:
            if self._on_toggle:
                self._on_toggle()
        
        def _on_settings_click(self, sender) -> None:
            if self._on_settings:
                self._on_settings()
        
        def _on_quit_click(self, sender) -> None:
            if self._on_quit:
                self._on_quit()
            rumps.quit_application()
        
        def _on_history_item_click(self, sender) -> None:
            if self._on_history_select and hasattr(sender, '_history_index'):
                self._on_history_select(sender._history_index)
        
        def set_status(self, status: str, message: str = "") -> None:
            self._status = status
            
            icon_path = self._get_icon_path(status)
            if icon_path:
                self.icon = icon_path
            else:
                icons = {
                    self.STATUS_IDLE: "🎤",
                    self.STATUS_RECORDING: "🔴",
                    self.STATUS_PROCESSING: "⏳"
                }
                self.title = icons.get(status, "🎤")
            
            if status == self.STATUS_RECORDING:
                self._toggle_item.title = f"Stop Recording ({self._hotkey_display})"
            else:
                self._toggle_item.title = f"Start Recording ({self._hotkey_display})"
            
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
            self._update_history_menu(entries)
        
        def _update_history_menu(self, entries: List[str]) -> None:
            try:
                if hasattr(self._history_menu, '_menu') and self._history_menu._menu is not None:
                    self._history_menu.clear()
                else:
                    for key in list(self._history_menu.keys()):
                        del self._history_menu[key]
            except Exception:
                pass
            
            if not entries:
                empty_item = rumps.MenuItem("No history")
                empty_item.set_callback(None)
                self._history_menu[empty_item.title] = empty_item
                return
            
            for i, entry in enumerate(entries[:10]):
                item = rumps.MenuItem(entry, callback=self._on_history_item_click)
                item._history_index = i
                self._history_menu[entry] = item
        
        def set_hotkey_display(self, display: str) -> None:
            self._hotkey_display = display
            self.set_status(self._status)
        
        def show_notification(self, title: str, message: str) -> None:
            rumps.notification(title=title, subtitle="", message=message)
        
        def show_alert(self, title: str, message: str) -> None:
            rumps.alert(title=title, message=message)

else:
    # Windows/Linux implementation using pystray
    import threading
    
    class MenuBarApp:
        """System Tray application for MWhisper (Windows/Linux)"""
        
        STATUS_IDLE = STATUS_IDLE
        STATUS_RECORDING = STATUS_RECORDING
        STATUS_PROCESSING = STATUS_PROCESSING
        
        def __init__(
            self,
            on_toggle: Optional[Callable[[], None]] = None,
            on_settings: Optional[Callable[[], None]] = None,
            on_history_select: Optional[Callable[[int], None]] = None,
            on_change_hotkey: Optional[Callable[[], None]] = None,
            on_quit: Optional[Callable[[], None]] = None,
            on_tick: Optional[Callable, None] = None
        ):
            self._status = self.STATUS_IDLE
            self._on_toggle = on_toggle
            self._on_settings = on_settings
            self._on_history_select = on_history_select
            self._on_change_hotkey = on_change_hotkey
            self._on_quit = on_quit
            self._on_tick = on_tick
            
            self._hotkey_display = "Ctrl+Shift+D"
            self._icon = None
            self._running = False
            self._history_entries = []
            
        def _get_icon(self, status: str = "idle"):
            """Get icon for current status"""
            from PIL import Image
            import sys
            
            if hasattr(sys, '_MEIPASS'):
                app_dir = Path(sys._MEIPASS)
            else:
                app_dir = Path(__file__).parent.parent
            
            icon_files = {
                "idle": "menu_icon_idle.png",
                "recording": "menu_icon_recording_0.png",
                "processing": "menu_icon_ready.png",
            }
            
            icon_path = app_dir / "assets" / icon_files.get(status, "menu_icon_idle.png")
            
            if icon_path.exists():
                return Image.open(str(icon_path))
            else:
                # Create a simple colored icon as fallback
                img = Image.new('RGB', (64, 64), 
                    color={'idle': 'green', 'recording': 'red', 'processing': 'yellow'}.get(status, 'gray'))
                return img
        
        def _build_menu(self):
            """Build the context menu"""
            from pystray import MenuItem, Menu
            
            def on_toggle(icon, item):
                if self._on_toggle:
                    self._on_toggle()
            
            def on_settings(icon, item):
                if self._on_settings:
                    self._on_settings()
            
            def on_quit(icon, item):
                if self._on_quit:
                    self._on_quit()
                self.stop()
            
            toggle_text = "Stop Recording" if self._status == self.STATUS_RECORDING else "Start Recording"
            
            menu_items = [
                MenuItem(f"{toggle_text} ({self._hotkey_display})", on_toggle),
                Menu.SEPARATOR,
                MenuItem(f"Status: {self._get_status_text()}", None, enabled=False),
                Menu.SEPARATOR,
                MenuItem("Settings...", on_settings),
                Menu.SEPARATOR,
                MenuItem("v26-crossplatform", None, enabled=False),
                MenuItem("Quit MWhisper", on_quit),
            ]
            
            return Menu(*menu_items)
        
        def _get_status_text(self) -> str:
            status_map = {
                self.STATUS_IDLE: "Ready",
                self.STATUS_RECORDING: "Recording...",
                self.STATUS_PROCESSING: "Processing..."
            }
            return status_map.get(self._status, "Ready")
        
        def run(self):
            """Start the system tray icon"""
            from pystray import Icon
            
            self._icon = Icon(
                "MWhisper",
                self._get_icon(self._status),
                "MWhisper",
                self._build_menu()
            )
            
            self._running = True
            
            # Start tick timer in background
            if self._on_tick:
                def tick_loop():
                    import time
                    while self._running:
                        time.sleep(0.5)
                        if self._on_tick:
                            self._on_tick(None)
                threading.Thread(target=tick_loop, daemon=True).start()
            
            self._icon.run()
        
        def stop(self):
            """Stop the system tray icon"""
            self._running = False
            if self._icon:
                self._icon.stop()
        
        def set_status(self, status: str, message: str = "") -> None:
            """Update status"""
            self._status = status
            if self._icon:
                self._icon.icon = self._get_icon(status)
                self._icon.menu = self._build_menu()
        
        def update_history_menu(self, entries: List[str]) -> None:
            """Update history entries"""
            self._history_entries = entries[:10]
            if self._icon:
                self._icon.menu = self._build_menu()
        
        def set_hotkey_display(self, display: str) -> None:
            """Update hotkey display string"""
            self._hotkey_display = display
            if self._icon:
                self._icon.menu = self._build_menu()
        
        def show_notification(self, title: str, message: str) -> None:
            """Show a notification"""
            if self._icon:
                self._icon.notify(message, title)
        
        def show_alert(self, title: str, message: str) -> None:
            """Show an alert dialog"""
            try:
                import tkinter as tk
                from tkinter import messagebox
                
                root = tk.Tk()
                root.withdraw()
                messagebox.showinfo(title, message)
                root.destroy()
            except:
                print(f"Alert: {title} - {message}")


def create_menu_bar_app(
    on_toggle: Optional[Callable[[], None]] = None,
    on_settings: Optional[Callable[[], None]] = None,
    on_history_select: Optional[Callable[[int], None]] = None,
    on_change_hotkey: Optional[Callable[[], None]] = None,
    on_quit: Optional[Callable[[], None]] = None,
    on_tick: Optional[Callable, None] = None
) -> MenuBarApp:
    """
    Create and return a MenuBarApp instance.
    Works on both macOS and Windows.
    """
    return MenuBarApp(
        on_toggle=on_toggle,
        on_settings=on_settings,
        on_history_select=on_history_select,
        on_change_hotkey=on_change_hotkey,
        on_quit=on_quit,
        on_tick=on_tick
    )


if __name__ == "__main__":
    def toggle():
        print("Toggle recording!")
    
    app = create_menu_bar_app(on_toggle=toggle)
    app.run()
