"""
MWhisper Main Application
Coordinating module that ties all components together
"""

import time
import threading
import subprocess
from typing import Optional
import numpy as np

from .audio_capture import AudioCapture, get_audio_level
from .transcriber import Transcriber
from .filler_filter import filter_fillers
from .hotkeys import HotkeyManager, PushToTalkHotkey
from .text_inserter import TextInserter
from .settings import Settings, get_settings
from .history import DictationHistory, get_history
from .menu_bar import MenuBarApp, create_menu_bar_app
from .translator import Translator
from .settings_window import show_settings_window


def check_accessibility_permission() -> bool:
    """
    Check if accessibility permission is granted.
    If not, prompts macOS to show the permission dialog.
    Returns True if permission is granted.
    """
    try:
        import ctypes
        import ctypes.util
        from Foundation import NSDictionary
        
        # Load ApplicationServices framework
        app_services = ctypes.cdll.LoadLibrary(
            '/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices'
        )
        
        # Get CoreFoundation for CFRelease
        cf = ctypes.cdll.LoadLibrary(ctypes.util.find_library('CoreFoundation'))
        
        # Define AXIsProcessTrustedWithOptions
        AXIsProcessTrustedWithOptions = app_services.AXIsProcessTrustedWithOptions
        AXIsProcessTrustedWithOptions.argtypes = [ctypes.c_void_p]
        AXIsProcessTrustedWithOptions.restype = ctypes.c_bool
        
        # kAXTrustedCheckOptionPrompt constant
        kAXTrustedCheckOptionPrompt = "AXTrustedCheckOptionPrompt"
        
        # Create options dict with prompt=True to trigger dialog
        # Using PyObjC to create the dictionary
        options = NSDictionary.dictionaryWithObject_forKey_(True, kAXTrustedCheckOptionPrompt)
        
        # Get the pointer to the NSDictionary for ctypes
        import objc
        options_ptr = objc.pyobjc_id(options)
        
        # Call AXIsProcessTrustedWithOptions - this triggers the dialog!
        is_trusted = AXIsProcessTrustedWithOptions(options_ptr)
        
        if not is_trusted:
            print("\n⚠️  Accessibility permission required!")
            print("A permission dialog should appear.")
            print("\n📋 If no dialog appeared:")
            print("1. Open System Preferences → Security & Privacy → Privacy → Accessibility")
            print("2. Click the lock 🔒 and enter your password")
            print("3. Add MWhisper.app (or Terminal if running from terminal)")
            print("4. Restart MWhisper\n")
            return False
        
        print("✓ Accessibility permission granted")
        return True
        
    except Exception as e:
        print(f"Warning: Could not check accessibility permission: {e}")
        # Fallback: try opening System Preferences directly
        print("Opening System Preferences...")
        subprocess.run([
            'open',
            'x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility'
        ])
        return False


def open_input_monitoring_settings():
    """Open System Settings → Input Monitoring for hotkey permissions"""
    print("\n⚠️  Input Monitoring permission may be required for hotkeys!")
    print("Opening System Settings → Input Monitoring...")
    subprocess.run([
        'open',
        'x-apple.systempreferences:com.apple.preference.security?Privacy_ListenEvent'
    ])


class MWhisperApp:
    """Main application class that coordinates all components"""
    
    def __init__(self, settings: Optional[Settings] = None):
        """
        Initialize MWhisper application.
        
        Args:
            settings: Settings instance (uses default if None)
        """
        self.settings = settings or get_settings()
        self.history = get_history(max_size=self.settings.history_size)
        
        # Components (lazy loaded)
        self._transcriber: Optional[Transcriber] = None
        self._audio_capture: Optional[AudioCapture] = None
        self._dictate_hotkey: Optional[PushToTalkHotkey] = None
        self._translate_hotkey: Optional[PushToTalkHotkey] = None
        self._hotkey_manager: Optional[HotkeyManager] = None  # For change_hotkey
        self._text_inserter: Optional[TextInserter] = None
        self._menu_app: Optional[MenuBarApp] = None
        self._translator: Optional[Translator] = None
        
        # State
        self._is_recording = False
        self._is_translate_recording = False
        self._recording_start_time = 0.0
        self._lock = threading.Lock()
    
    def _ensure_transcriber(self) -> Transcriber:
        """Lazy load transcriber"""
        if self._transcriber is None:
            print("Loading Parakeet-MLX model...")
            self._transcriber = Transcriber(language=self.settings.language)
        return self._transcriber
    
    def _ensure_audio_capture(self) -> AudioCapture:
        """Lazy load audio capture"""
        if self._audio_capture is None:
            self._audio_capture = AudioCapture(
                device_id=self.settings.microphone_id,
                sample_rate=16000
            )
        return self._audio_capture
    
    def _ensure_text_inserter(self) -> TextInserter:
        """Lazy load text inserter"""
        if self._text_inserter is None:
            method = self.settings.get("insertion_method", "keystroke")
            self._text_inserter = TextInserter(method=method)
        return self._text_inserter
    
    def toggle_recording(self) -> None:
        """Toggle recording on/off"""
        with self._lock:
            if self._is_recording:
                self._stop_recording()
            else:
                self._start_recording()
    
    def toggle_translate_recording(self) -> None:
        """Toggle translate recording on/off"""
        with self._lock:
            if self._is_translate_recording:
                self._stop_translate_recording()
            else:
                self._start_translate_recording()
    
    def _start_recording(self) -> None:
        """Start recording from microphone"""
        print("\n🎤 Starting recording...")
        
        self._is_recording = True
        self._recording_start_time = time.time()
        
        # Update UI
        if self._menu_app:
            self._menu_app.set_status(
                MenuBarApp.STATUS_RECORDING,
                "Recording..."
            )
        
        # Start audio capture
        audio = self._ensure_audio_capture()
        audio.start()
    
    def _stop_recording(self) -> None:
        """Stop recording and process audio"""
        print("⏹ Stopping recording...")
        
        # Get recorded audio
        audio = self._ensure_audio_capture()
        audio_data = audio.stop()
        
        duration = time.time() - self._recording_start_time
        self._is_recording = False
        
        # Update UI
        if self._menu_app:
            self._menu_app.set_status(
                MenuBarApp.STATUS_PROCESSING,
                "Transcribing..."
            )
        
        # Process in background
        threading.Thread(
            target=self._process_audio,
            args=(audio_data, duration),
            daemon=True
        ).start()
    
    def _start_translate_recording(self) -> None:
        """Start recording for translation"""
        print("\n🌐 Starting translate recording...")
        
        self._is_translate_recording = True
        self._recording_start_time = time.time()
        
        # Update UI
        if self._menu_app:
            self._menu_app.set_status(
                MenuBarApp.STATUS_RECORDING,
                "Recording for translation..."
            )
        
        # Start audio capture
        audio = self._ensure_audio_capture()
        audio.start()
    
    def _stop_translate_recording(self) -> None:
        """Stop recording and process for translation"""
        print("⏹ Stopping translate recording...")
        
        # Get recorded audio
        audio = self._ensure_audio_capture()
        audio_data = audio.stop()
        
        duration = time.time() - self._recording_start_time
        self._is_translate_recording = False
        
        # Update UI
        if self._menu_app:
            self._menu_app.set_status(
                MenuBarApp.STATUS_PROCESSING,
                "Translating..."
            )
        
        # Process in background with translation
        threading.Thread(
            target=self._process_audio_for_translation,
            args=(audio_data, duration),
            daemon=True
        ).start()
    
    def _process_audio_for_translation(self, audio_data: np.ndarray, duration: float) -> None:
        """Process recorded audio and translate"""
        try:
            if len(audio_data) == 0:
                print("No audio recorded")
                self._on_translation_complete("", duration)
                return
            
            # Check audio level
            level = get_audio_level(audio_data)
            if level < -50:
                print(f"Audio too quiet: {level:.1f} dB")
                self._on_translation_complete("", duration)
                return
            
            print(f"Processing {len(audio_data)} samples ({duration:.1f}s)...")
            
            # Transcribe
            transcriber = self._ensure_transcriber()
            result = transcriber.transcribe(audio_data)
            
            text = result.get("text", "")
            print(f"Transcription: {text}")
            
            # Filter filler words
            if self.settings.filter_fillers:
                text = filter_fillers(text)
            
            if not text:
                self._on_translation_complete("", duration)
                return
            
            # Translate via OpenAI
            api_key = self.settings.get("openai_api_key", "")
            if not api_key:
                print("Error: OpenAI API key not configured")
                if self._menu_app:
                    self._menu_app.show_alert(
                        "API Key Required",
                        "Please set your OpenAI API key in Settings."
                    )
                self._on_translation_complete("", duration)
                return
            
            prompt = self.settings.get("translation_prompt", "")
            if self._translator is None:
                self._translator = Translator(api_key, prompt)
            
            translated = self._translator.translate(text)
            self._on_translation_complete(translated or "", duration)
            
        except Exception as e:
            print(f"Translation processing error: {e}")
            import traceback
            traceback.print_exc()
            self._on_translation_complete("", duration)
    
    def _on_translation_complete(self, text: str, duration: float) -> None:
        """Handle translation completion"""
        # Update UI
        if self._menu_app:
            self._menu_app.set_status(MenuBarApp.STATUS_IDLE, "Ready")
        
        if not text:
            print("No translation to insert")
            return
        
        # Add to history (Translation)
        self.history.add(f"[EN] {text}", duration, "en")
        
        # Update history menu
        if self._menu_app:
            history_items = [str(e) for e in self.history.get_recent(10)]
            self._menu_app.update_history_menu(history_items)
        
        # Insert translated text
        print(f"Inserting translation: {text}")
        inserter = self._ensure_text_inserter()
        success = inserter.insert(text)
        
        if success:
            print("✓ Translation inserted successfully")
            if self._menu_app:
                self._menu_app.show_notification(
                    "MWhisper Translation",
                    f"Inserted: {text[:50]}..."
                )
        else:
            print("✗ Failed to insert translation")
    
    def _process_audio(self, audio_data: np.ndarray, duration: float) -> None:
        """Process recorded audio"""
        try:
            if len(audio_data) == 0:
                print("No audio recorded")
                self._on_processing_complete("", duration)
                return
            
            # Check audio level
            level = get_audio_level(audio_data)
            if level < -50:  # Very quiet
                print(f"Audio too quiet: {level:.1f} dB")
                self._on_processing_complete("", duration)
                return
            
            print(f"Processing {len(audio_data)} samples ({duration:.1f}s)...")
            
            # Transcribe
            transcriber = self._ensure_transcriber()
            result = transcriber.transcribe(audio_data)
            
            text = result.get("text", "")
            language = result.get("language", "unknown")
            
            print(f"Raw transcription: {text}")
            
            # Filter filler words
            if self.settings.filter_fillers:
                text = filter_fillers(text)
                print(f"Filtered: {text}")
            
            self._on_processing_complete(text, duration, language)
            
        except Exception as e:
            print(f"Processing error: {e}")
            self._on_processing_complete("", duration)
    
    def _on_processing_complete(
        self,
        text: str,
        duration: float,
        language: str = "unknown"
    ) -> None:
        """Handle processing completion"""
        # Update UI
        if self._menu_app:
            self._menu_app.set_status(MenuBarApp.STATUS_IDLE, "Ready")
        
        if not text:
            print("No text to insert")
            return
        
        # Add to history
        self.history.add(text, duration, language)
        
        # Update history menu
        if self._menu_app:
            history_items = [str(e) for e in self.history.get_recent(10)]
            self._menu_app.update_history_menu(history_items)
        
        # Insert text
        print(f"Inserting: {text}")
        inserter = self._ensure_text_inserter()
        success = inserter.insert(text)
        
        if success:
            print("✓ Text inserted successfully")
            if self._menu_app:
                self._menu_app.show_notification(
                    "MWhisper",
                    f"Inserted: {text[:50]}..."
                )
        else:
            print("✗ Failed to insert text")
    
    def _on_history_select(self, index: int) -> None:
        """Handle history item selection"""
        entry = self.history.get_by_index(index)
        if entry:
            inserter = self._ensure_text_inserter()
            inserter.insert(entry.text)
    
    def _on_settings(self) -> None:
        """Handle settings menu click"""
        # Launch settings GUI in a separate process
        import subprocess
        import sys
        import os
        
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings_gui.py")
        
        def run_settings():
            try:
                # Use the same python interpreter (or app binary)
                cmd = [sys.executable, "--settings"]
                
                # If running from source (not frozen), we need the script path ??
                # Actually main.py handles it. If not frozen, sys.executable is python.
                # If not frozen, we need: python main.py --settings
                if not getattr(sys, 'frozen', False):
                    main_script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "main.py")
                    cmd = [sys.executable, main_script, "--settings"]
                
                print(f"Launching settings with: {cmd}")
                
                process = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True
                )
                
                if process.returncode == 0:
                    print("Settings saved, reloading...")
                    # Schedule reload on main thread (actually this is a thread, so can call methods)
                    # Use rumps timer or just direct call if thread-safe
                    self._reload_settings()
                else:
                    if process.stderr:
                        print(f"Settings error: {process.stderr}")
            except Exception as e:
                print(f"Failed to launch settings: {e}")
        
        # Run in thread to not block menu
        threading.Thread(target=run_settings, daemon=True).start()

    def _reload_settings(self) -> None:
        """Reload settings from config file and update hotkeys"""
        print("Reloading settings...")
        self.settings.load()
        
        # Re-initialize hotkeys
        # Stop existing
        if self._dictate_hotkey:
            self._dictate_hotkey.stop()
        if self._translate_hotkey:
            self._translate_hotkey.stop()
            
        # Start new
        try:
            # Dictation Hotkey
            hotkey_str = self.settings.hotkey
            self._dictate_hotkey = PushToTalkHotkey(
                hotkey_str,
                on_press=self._start_recording,
                on_release=self._stop_recording
            )
            self._dictate_hotkey.start()
            
            # Translate Hotkey
            translate_hotkey_str = self.settings.get("translate_hotkey")
            if translate_hotkey_str:
                self._translate_hotkey = PushToTalkHotkey(
                    translate_hotkey_str,
                    on_press=self._start_translate_recording,
                    on_release=self._stop_translate_recording
                )
                self._translate_hotkey.start()
            
            # Update menu display
            if self._menu_app:
                mapping = {
                    '<cmd>': '⌘', '<cmd_r>': '⌘',
                    '<shift>': '⇧', '<shift_r>': '⇧',
                    '<ctrl>': '⌃', '<ctrl_r>': '⌃',
                    '<alt>': '⌥', '<alt_r>': '⌥',
                }
                display = hotkey_str
                for k, v in mapping.items():
                    display = display.replace(k, v).replace('+', '')
                display = display.upper()
                
                self._menu_app.set_hotkey_display(display)
                self._menu_app.show_notification("MWhisper", "Settings reloaded successfully")
                
        except Exception as e:
            print(f"Failed to apply new settings: {e}")
            if self._menu_app:
                self._menu_app.show_alert("Error", f"Failed to apply settings: {e}")
    
    def _on_quit(self) -> None:
        """Handle quit"""
        print("Shutting down...")
        
        # Stop hotkey listener
        if self._hotkey_manager:
            self._hotkey_manager.stop()
        
        # Stop recording if active
        if self._is_recording and self._audio_capture:
            self._audio_capture.stop()
    
    def _on_change_hotkey(self) -> None:
        """Handle change hotkey request"""
        print("🔧 Change hotkey requested")
        
        # Show alert to notify user
        if self._menu_app:
            self._menu_app.show_alert(
                "Change Hotkey",
                "After closing this dialog, press your new key combination.\n\nYou have 10 seconds."
            )
        
        print("🔧 Starting hotkey capture...")
        
        # Stop current hotkey listener to avoid conflicts
        if self._hotkey_manager:
            self._hotkey_manager.stop()
        
        def on_hotkey_captured(pynput_format: str, display_format: str):
            print(f"🔧 Hotkey captured: {pynput_format} ({display_format})")
            if pynput_format and display_format:
                # Save new hotkey to settings
                self.settings.set("hotkey", pynput_format)
                
                # Update hotkey manager
                if self._hotkey_manager:
                    self._hotkey_manager.set_hotkey(pynput_format)
                    self._hotkey_manager.start()
                
                # Update menu display
                if self._menu_app:
                    self._menu_app.set_hotkey_display(display_format)
                    self._menu_app.show_alert(
                        "Hotkey Changed",
                        f"New hotkey: {display_format}"
                    )
                
                print(f"✓ Hotkey changed to: {display_format}")
            else:
                print("🔧 Hotkey capture timeout/cancelled")
                # Timeout or cancelled - restore previous hotkey
                if self._hotkey_manager:
                    self._hotkey_manager.start()
                
                if self._menu_app:
                    self._menu_app.show_alert(
                        "Hotkey Change Cancelled",
                        "No valid key combination detected."
                    )
        
        # Use existing hotkey manager to capture
        if self._hotkey_manager:
            self._hotkey_manager.capture_hotkey(on_hotkey_captured, timeout=10.0)
    
    def run(self) -> None:
        """Run the application"""
        print("=" * 50)
        print("MWhisper - Voice Dictation for Mac")
        print("=" * 50)
        
        # Pre-load transcriber (takes time)
        print("\nInitializing transcriber...")
        try:
            self._ensure_transcriber()
        except Exception as e:
            print(f"Warning: Could not load transcriber: {e}")
            print("Transcription will fail until model is loaded.")
        
        # Setup dictation hotkey (push-to-talk)
        self._dictate_hotkey = PushToTalkHotkey(
            hotkey=self.settings.hotkey,
            on_press=self._start_recording,
            on_release=self._stop_recording
        )
        self._dictate_hotkey.start()
        
        # Setup translate hotkey (push-to-talk)
        translate_hotkey = self.settings.get("translate_hotkey", "<cmd>+<shift>+u")
        self._translate_hotkey = PushToTalkHotkey(
            hotkey=translate_hotkey,
            on_press=self._start_translate_recording,
            on_release=self._stop_translate_recording
        )
        self._translate_hotkey.start()
        
        # Legacy hotkey manager for change_hotkey functionality
        self._hotkey_manager = HotkeyManager(
            callback=lambda: None,
            hotkey=self.settings.hotkey
        )
        
        # Create menu bar app
        self._menu_app = create_menu_bar_app(
            on_toggle=self.toggle_recording,
            on_settings=self._on_settings,
            on_history_select=self._on_history_select,
            on_change_hotkey=self._on_change_hotkey,
            on_quit=self._on_quit
        )
        
        # Set hotkey display
        self._menu_app.set_hotkey_display(
            self._dictate_hotkey.get_display_string()
        )
        
        # Update history menu
        history_items = [str(e) for e in self.history.get_recent(10)]
        self._menu_app.update_history_menu(history_items)
        
        print(f"\n✓ Ready! (Push-to-talk mode)")
        print(f"  {self._dictate_hotkey.get_display_string()} — Hold to dictate")
        print(f"  {self._translate_hotkey.get_display_string()} — Hold to dictate + translate")
        print("Click the menu bar icon for options.\n")
        
        # Run menu bar app (blocking)
        self._menu_app.run()


def run_app() -> None:
    """Entry point to run the application"""
    # Check accessibility permission first
    if not check_accessibility_permission():
        print("Please grant Accessibility permission and restart the app.")
        # Still run the app, but hotkeys may not work
    
    try:
        app = MWhisperApp()
        app.run()
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}")
        raise
