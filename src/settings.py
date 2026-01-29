"""
MWhisper Settings Manager
Handles loading and saving user preferences
"""

import json
import os
from typing import Any, Dict, Optional
from pathlib import Path


# Default settings
DEFAULT_SETTINGS: Dict[str, Any] = {
    "hotkey": "<cmd>+<shift>+d",
    "translate_hotkey": "<cmd>+<shift>+t",
    "microphone_id": None,
    "language": "auto",
    "filter_fillers": True,
    "history_size": 20,
    "auto_start": False,
    "show_realtime_text": False,
    "insertion_method": "keystroke",  # "keystroke" or "clipboard"
    "sound_feedback": True,
    # OpenAI settings
    "openai_api_key": "",
    "translation_prompt": "Переведи этот текст на английский язык. Исправь ошибки и напиши простыми словами. Верни ТОЛЬКО перевод, без пояснений.",
    # Custom Actions: List[Dict[str, str]] (id, name, hotkey, prompt)
    "custom_actions": [],
}


class Settings:
    """Manages application settings"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize settings manager.
        
        Args:
            config_path: Path to config file (default: config.json in app dir)
        """
        if config_path:
            self.config_path = Path(config_path)
        else:
            # Use app directory
            app_dir = Path(__file__).parent.parent
            self.config_path = app_dir / "config.json"
        
        self._settings: Dict[str, Any] = DEFAULT_SETTINGS.copy()
        self.load()
    
    def load(self) -> bool:
        """
        Load settings from config file.
        
        Returns:
            True if loaded successfully, False if using defaults
        """
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                
                # Merge with defaults (to handle new settings)
                for key, value in loaded.items():
                    if key in DEFAULT_SETTINGS:
                        self._settings[key] = value
                
                print(f"✓ Settings loaded from {self.config_path}")
                return True
        except Exception as e:
            print(f"Failed to load settings: {e}")
        
        return False
    
    def save(self) -> bool:
        """
        Save current settings to config file.
        
        Returns:
            True if saved successfully
        """
        try:
            # Ensure directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, indent=4, ensure_ascii=False)
            
            print(f"✓ Settings saved to {self.config_path}")
            return True
        except Exception as e:
            print(f"Failed to save settings: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value"""
        return self._settings.get(key, default)
    
    def set(self, key: str, value: Any, save_now: bool = True) -> None:
        """
        Set a setting value.
        
        Args:
            key: Setting key
            value: Setting value
            save_now: If True, save to file immediately
        """
        self._settings[key] = value
        if save_now:
            self.save()
    
    def reset(self, key: Optional[str] = None) -> None:
        """
        Reset setting(s) to default.
        
        Args:
            key: Specific key to reset, or None for all
        """
        if key:
            if key in DEFAULT_SETTINGS:
                self._settings[key] = DEFAULT_SETTINGS[key]
        else:
            self._settings = DEFAULT_SETTINGS.copy()
        self.save()
    
    def get_all(self) -> Dict[str, Any]:
        """Get all settings as dictionary"""
        return self._settings.copy()
    
    # Convenience properties
    @property
    def hotkey(self) -> str:
        return self.get("hotkey", "<cmd>+<shift>+d")
    
    @hotkey.setter
    def hotkey(self, value: str) -> None:
        self.set("hotkey", value)
    
    @property
    def microphone_id(self) -> Optional[int]:
        return self.get("microphone_id")
    
    @microphone_id.setter
    def microphone_id(self, value: Optional[int]) -> None:
        self.set("microphone_id", value)
    
    @property
    def language(self) -> str:
        return self.get("language", "auto")
    
    @language.setter
    def language(self, value: str) -> None:
        self.set("language", value)
    
    @property
    def filter_fillers(self) -> bool:
        return self.get("filter_fillers", True)
    
    @filter_fillers.setter
    def filter_fillers(self, value: bool) -> None:
        self.set("filter_fillers", value)
    
    @property
    def history_size(self) -> int:
        return self.get("history_size", 20)
    
    @property
    def auto_start(self) -> bool:
        return self.get("auto_start", False)
    
    @auto_start.setter
    def auto_start(self, value: bool) -> None:
        self.set("auto_start", value)

    @property
    def custom_actions(self) -> list:
        return self.get("custom_actions", [])

    @custom_actions.setter
    def custom_actions(self, value: list) -> None:
        self.set("custom_actions", value)


# Singleton instance
_settings_instance: Optional[Settings] = None


def get_settings(config_path: Optional[str] = None) -> Settings:
    """Get or create singleton settings instance"""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings(config_path)
    return _settings_instance
