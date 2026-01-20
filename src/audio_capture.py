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
    
    def _resolve_device_id(self) -> Optional[int]:
        """
        Resolve and validate the device ID before starting recording.
        
        When audio devices are connected/disconnected, device IDs can shift.
        This method validates the saved device_id is still valid, and falls
        back to the system default if not.
        
        Returns:
            Valid device ID to use, or None for system default
        """
        import sounddevice as sd
        
        # Refresh device list
        try:
            sd.query_devices()
        except Exception as e:
            print(f"Warning: Failed to query devices: {e}")
            return self.device_id
        
        # If no specific device set, use system default
        if self.device_id is None:
            return None
        
        # Validate the saved device_id still exists and is an input device
        try:
            devices = sd.query_devices()
            if self.device_id < len(devices):
                dev = devices[self.device_id]
                if dev['max_input_channels'] > 0:
                    # Device ID is valid and is an input device
                    print(f"✓ Using saved device {self.device_id}: {dev['name']}")
                    return self.device_id
                else:
                    print(f"⚠ Device {self.device_id} is not an input device, using default")
            else:
                print(f"⚠ Device ID {self.device_id} no longer exists, using default")
        except Exception as e:
            print(f"Warning: Device validation failed: {e}")
        
        # Fall back to system default
        try:
            default_id = sd.default.device[0]
            if default_id is not None:
                dev_name = sd.query_devices(default_id)['name']
                print(f"↪ Falling back to default device {default_id}: {dev_name}")
                return default_id
        except Exception as e:
            print(f"Warning: Could not get default device: {e}")
        
        return None
    
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
        
        # Dynamically resolve the device ID (handles hot-plug scenarios)
        resolved_device = self._resolve_device_id()
        
        try:
            self._stream = sd.InputStream(
                device=resolved_device,
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=np.float32,
                blocksize=self.chunk_size,
                callback=self._audio_callback
            )
        except Exception as e:
            print(f"Warning: Stream start failed with device {resolved_device}: {e}")
            # Try with system default as last resort
            print("Attempting to use system default device...")
            try:
                sd.query_devices()
                default_id = sd.default.device[0]
                print(f"Using fallback default device: {default_id}")
                
                self._stream = sd.InputStream(
                    device=default_id,
                    samplerate=self.sample_rate,
                    channels=self.channels,
                    dtype=np.float32,
                    blocksize=self.chunk_size,
                    callback=self._audio_callback
                )
                print("✓ Audio recovery successful")
            except Exception as e2:
                print(f"Critical: Audio recovery failed: {e2}")
                self._is_recording = False
                raise e2
                
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
