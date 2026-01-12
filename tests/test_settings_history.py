"""
Tests for settings and history modules
"""

import pytest
import json
import tempfile
from pathlib import Path


class TestSettings:
    """Test cases for settings module"""
    
    def test_default_settings(self):
        """Test that default settings are applied"""
        from src.settings import Settings
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            settings = Settings(f.name)
        
        assert settings.hotkey == "<cmd>+<shift>+d"
        assert settings.language == "auto"
        assert settings.filter_fillers is True
    
    def test_save_and_load(self):
        """Test saving and loading settings"""
        from src.settings import Settings
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_path = f.name
        
        # Create and modify settings
        settings1 = Settings(temp_path)
        settings1.hotkey = "<ctrl>+<alt>+r"
        settings1.language = "ru"
        settings1.save()
        
        # Load in new instance
        settings2 = Settings(temp_path)
        assert settings2.hotkey == "<ctrl>+<alt>+r"
        assert settings2.language == "ru"
        
        # Cleanup
        Path(temp_path).unlink()
    
    def test_get_set(self):
        """Test get and set methods"""
        from src.settings import Settings
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            settings = Settings(f.name)
        
        settings.set("custom_key", "custom_value", save_now=False)
        assert settings.get("custom_key") == "custom_value"
        assert settings.get("nonexistent", "default") == "default"
    
    def test_reset(self):
        """Test resetting settings"""
        from src.settings import Settings, DEFAULT_SETTINGS
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            settings = Settings(f.name)
        
        settings.hotkey = "changed"
        settings.reset("hotkey")
        assert settings.hotkey == DEFAULT_SETTINGS["hotkey"]


class TestHistory:
    """Test cases for history module"""
    
    def test_add_entry(self):
        """Test adding history entries"""
        from src.history import DictationHistory
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            history = DictationHistory(f.name, max_size=5)
        
        entry = history.add("Test text", duration=2.5, language="en")
        assert entry.text == "Test text"
        assert entry.duration == 2.5
        assert len(history) == 1
    
    def test_max_size(self):
        """Test history max size limit"""
        from src.history import DictationHistory
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            history = DictationHistory(f.name, max_size=3)
        
        for i in range(5):
            history.add(f"Entry {i}")
        
        assert len(history) == 3
        # Most recent should be first
        assert "Entry 4" in history.get_by_index(0).text
    
    def test_clear(self):
        """Test clearing history"""
        from src.history import DictationHistory
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            history = DictationHistory(f.name)
        
        history.add("Test")
        history.clear()
        assert len(history) == 0
    
    def test_persistence(self):
        """Test history persistence"""
        from src.history import DictationHistory
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_path = f.name
        
        # Add entries
        history1 = DictationHistory(temp_path)
        history1.add("Persisted text")
        
        # Load in new instance
        history2 = DictationHistory(temp_path)
        assert len(history2) == 1
        assert history2.get_by_index(0).text == "Persisted text"
        
        Path(temp_path).unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
