"""
MWhisper Audio Capture Module
Handles microphone input using sounddevice
"""

import numpy as np
import threading
from typing import Optional, Callable, List, Dict
from queue import Queue


class AudioCapture:
    """Microphone audio capture using sounddevice"""
    
    def __init__(
        self,
        device_id: Optional[int] = None,
        sample_rate: int = 16000,
        channels: int = 1,
        chunk_duration: float = 0.5
    ):
        """
        Initialize audio capture.
        
        Args:
            device_id: Microphone device ID (None for default)
            sample_rate: Sample rate in Hz (16000 recommended for Parakeet)
            channels: Number of channels (1 for mono)
            chunk_duration: Duration of each audio chunk in seconds
        """
        self.device_id = device_id
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_duration = chunk_duration
        self.chunk_size = int(sample_rate * chunk_duration)
        
        self._stream = None
        self._audio_buffer: List[np.ndarray] = []
        self._audio_queue: Queue = Queue()
        self._is_recording = False
        self._lock = threading.Lock()
        
        # Callback for real-time processing
        self._on_audio_callback: Optional[Callable[[np.ndarray], None]] = None
    
    def _audio_callback(self, indata, frames, time_info, status):
        """Callback for sounddevice stream"""
        if status:
            print(f"Audio status: {status}")
        
        # Copy audio data
        audio_chunk = indata[:, 0].copy() if self.channels == 1 else indata.copy()
        
        with self._lock:
            if self._is_recording:
                self._audio_buffer.append(audio_chunk)
                self._audio_queue.put(audio_chunk)
                
                # Call real-time callback if set
                if self._on_audio_callback:
                    self._on_audio_callback(audio_chunk)
    
    def start(self, on_audio: Optional[Callable[[np.ndarray], None]] = None) -> None:
        """
        Start recording from microphone.
        
        Args:
            on_audio: Optional callback for real-time audio chunks
        """
        import sounddevice as sd
        
        self._on_audio_callback = on_audio
        self._audio_buffer = []
        
        # Clear queue
        while not self._audio_queue.empty():
            self._audio_queue.get_nowait()
        
        self._is_recording = True
        
        self._stream = sd.InputStream(
            device=self.device_id,
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype=np.float32,
            blocksize=self.chunk_size,
            callback=self._audio_callback
        )
        self._stream.start()
        print("🎤 Recording started")
    
    def stop(self) -> np.ndarray:
        """
        Stop recording and return captured audio.
        
        Returns:
            Complete audio as numpy array
        """
        self._is_recording = False
        
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        
        print("⏹ Recording stopped")
        
        with self._lock:
            if self._audio_buffer:
                return np.concatenate(self._audio_buffer)
            return np.array([], dtype=np.float32)
    
    def is_recording(self) -> bool:
        """Check if currently recording"""
        return self._is_recording
    
    def get_audio_chunk(self, timeout: float = 1.0) -> Optional[np.ndarray]:
        """
        Get next audio chunk from queue.
        
        Args:
            timeout: Timeout in seconds
        
        Returns:
            Audio chunk or None if timeout
        """
        try:
            return self._audio_queue.get(timeout=timeout)
        except:
            return None
    
    def set_device(self, device_id: Optional[int]) -> None:
        """Set the recording device"""
        was_recording = self._is_recording
        if was_recording:
            self.stop()
        
        self.device_id = device_id
        
        if was_recording:
            self.start(self._on_audio_callback)
    
    @staticmethod
    def get_devices() -> List[Dict]:
        """
        Get list of available audio input devices.
        
        Returns:
            List of device info dicts with 'id', 'name', 'channels'
        """
        import sounddevice as sd
        
        devices = []
        for i, dev in enumerate(sd.query_devices()):
            if dev['max_input_channels'] > 0:
                devices.append({
                    'id': i,
                    'name': dev['name'],
                    'channels': dev['max_input_channels'],
                    'sample_rate': dev['default_samplerate']
                })
        return devices
    
    @staticmethod
    def get_default_device() -> Optional[Dict]:
        """Get default input device info"""
        import sounddevice as sd
        
        try:
            default_id = sd.default.device[0]
            if default_id is not None:
                dev = sd.query_devices(default_id)
                return {
                    'id': default_id,
                    'name': dev['name'],
                    'channels': dev['max_input_channels'],
                    'sample_rate': dev['default_samplerate']
                }
        except:
            pass
        return None


def get_audio_level(audio: np.ndarray) -> float:
    """
    Calculate audio level (RMS) in dB.
    
    Args:
        audio: Audio data
    
    Returns:
        Level in dB (0 to -inf)
    """
    if len(audio) == 0:
        return -100.0
    
    rms = np.sqrt(np.mean(audio ** 2))
    if rms > 0:
        return 20 * np.log10(rms)
    return -100.0
