"""
Tests for the audio capture module
"""

import pytest
import numpy as np


class TestAudioCapture:
    """Test cases for audio capture"""
    
    def test_get_devices(self):
        """Test listing audio devices"""
        from src.audio_capture import AudioCapture
        
        devices = AudioCapture.get_devices()
        assert isinstance(devices, list)
        
        # Each device should have required keys
        for device in devices:
            assert 'id' in device
            assert 'name' in device
            assert 'channels' in device
    
    def test_get_default_device(self):
        """Test getting default device"""
        from src.audio_capture import AudioCapture
        
        default = AudioCapture.get_default_device()
        # May be None if no audio devices
        if default:
            assert 'id' in default
            assert 'name' in default
    
    def test_audio_level_calculation(self):
        """Test audio level calculation"""
        from src.audio_capture import get_audio_level
        
        # Silent audio
        silent = np.zeros(1000, dtype=np.float32)
        level = get_audio_level(silent)
        assert level == -100.0
        
        # Full scale audio
        loud = np.ones(1000, dtype=np.float32)
        level = get_audio_level(loud)
        assert level == 0.0
        
        # Half scale
        half = np.ones(1000, dtype=np.float32) * 0.5
        level = get_audio_level(half)
        assert -10 < level < 0
    
    def test_audio_level_empty_array(self):
        """Test audio level with empty array"""
        from src.audio_capture import get_audio_level
        
        empty = np.array([], dtype=np.float32)
        level = get_audio_level(empty)
        assert level == -100.0


class TestAudioCaptureInitialization:
    """Test AudioCapture initialization"""
    
    def test_init_default(self):
        """Test default initialization"""
        from src.audio_capture import AudioCapture
        
        capture = AudioCapture()
        assert capture.sample_rate == 16000
        assert capture.channels == 1
        assert not capture.is_recording()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
