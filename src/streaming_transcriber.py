"""
MWhisper Streaming Transcriber Module
Uses whisper.cpp via pywhispercpp for real-time streaming transcription
"""

import os
import sys
import numpy as np
from typing import Optional, Callable, Dict, Any
from threading import Thread, Event
import queue
import sounddevice as sd


class StreamingTranscriber:
    """Real-time streaming speech-to-text using whisper.cpp"""
    
    # Default model - medium offers good balance of speed and quality
    DEFAULT_MODEL = "medium"
    
    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        language: str = "auto",
        on_partial: Optional[Callable[[str], None]] = None,
        on_final: Optional[Callable[[str], None]] = None
    ):
        """
        Initialize streaming transcriber with whisper.cpp.
        
        Args:
            model_name: Whisper model to use (tiny, base, small, medium, large-v3)
            language: Language code or "auto" for auto-detection
            on_partial: Callback for partial (in-progress) transcriptions
            on_final: Callback for final transcriptions
        """
        self.model_name = model_name
        self.language = language if language != "auto" else None
        self.on_partial = on_partial
        self.on_final = on_final
        
        self._model = None
        self._is_streaming = False
        self._stop_event = Event()
        self._audio_queue = queue.Queue()
        self._stream_thread: Optional[Thread] = None
        self._audio_stream = None
        
        # Audio parameters for whisper.cpp
        self.sample_rate = 16000
        self.chunk_duration = 0.3  # Process chunks every 300ms for faster response
        self.chunk_size = int(self.sample_rate * self.chunk_duration)
        
        # Buffer for accumulating audio
        self._audio_buffer = []
        self._min_audio_length = 0.5  # Minimum seconds before first transcription
        
        self._load_model()
    
    def _load_model(self) -> None:
        """Load the whisper.cpp model"""
        try:
            from pywhispercpp.model import Model
            
            print(f"Loading whisper.cpp model: {self.model_name}...")
            
            # Model will be downloaded automatically if not present
            self._model = Model(self.model_name, print_progress=True)
            
            print(f"✓ whisper.cpp model '{self.model_name}' loaded successfully")
            
        except ImportError as e:
            raise ImportError(
                f"pywhispercpp import failed: {e}. Run: pip install pywhispercpp"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to load whisper.cpp model: {e}")
    
    def _audio_callback(self, indata, frames, time_info, status):
        """Callback for audio stream - collects audio chunks"""
        if status:
            print(f"Audio status: {status}")
        
        # Add audio to buffer
        audio_chunk = indata[:, 0].copy()  # Mono
        self._audio_buffer.append(audio_chunk)
    
    def _process_stream(self) -> None:
        """Background thread that processes audio and generates transcriptions"""
        accumulated_text = ""
        last_transcription = ""
        
        while not self._stop_event.is_set():
            # Wait a bit for audio to accumulate
            self._stop_event.wait(self.chunk_duration)
            
            if self._stop_event.is_set():
                break
            
            # Check if we have enough audio
            if not self._audio_buffer:
                continue
            
            # Combine all buffered audio
            audio_data = np.concatenate(self._audio_buffer)
            total_duration = len(audio_data) / self.sample_rate
            
            # Skip if too short
            if total_duration < self._min_audio_length:
                continue
            
            try:
                # Transcribe accumulated audio
                # whisper.cpp expects audio as float32 normalized to [-1, 1]
                if audio_data.dtype != np.float32:
                    audio_data = audio_data.astype(np.float32)
                
                # Normalize
                max_val = np.max(np.abs(audio_data))
                if max_val > 0:
                    audio_data = audio_data / max_val
                
                # Transcribe
                segments = self._model.transcribe(
                    audio_data,
                    language=self.language
                )
                
                # Extract text from segments
                current_text = " ".join([seg.text.strip() for seg in segments])
                current_text = current_text.strip()
                
                # Emit partial result if text changed
                if current_text and current_text != last_transcription:
                    last_transcription = current_text
                    if self.on_partial:
                        self.on_partial(current_text)
                
            except Exception as e:
                print(f"Streaming transcription error: {e}")
        
        # Final transcription with all accumulated audio
        if self._audio_buffer:
            try:
                audio_data = np.concatenate(self._audio_buffer)
                if audio_data.dtype != np.float32:
                    audio_data = audio_data.astype(np.float32)
                
                max_val = np.max(np.abs(audio_data))
                if max_val > 0:
                    audio_data = audio_data / max_val
                
                segments = self._model.transcribe(
                    audio_data,
                    language=self.language
                )
                
                final_text = " ".join([seg.text.strip() for seg in segments])
                final_text = final_text.strip()
                
                if final_text and self.on_final:
                    self.on_final(final_text)
                    
            except Exception as e:
                print(f"Final transcription error: {e}")
    
    def start_streaming(self, device_id: Optional[int] = None) -> None:
        """Start real-time streaming transcription from microphone"""
        if self._is_streaming:
            print("Already streaming")
            return
        
        self._is_streaming = True
        self._stop_event.clear()
        self._audio_buffer = []
        
        # Force PortAudio reset for device changes
        try:
            sd._terminate()
            sd._initialize()
        except:
            pass
        
        # Start audio capture
        self._audio_stream = sd.InputStream(
            device=device_id,
            samplerate=self.sample_rate,
            channels=1,
            dtype=np.float32,
            blocksize=self.chunk_size,
            callback=self._audio_callback
        )
        self._audio_stream.start()
        
        # Start processing thread
        self._stream_thread = Thread(target=self._process_stream, daemon=True)
        self._stream_thread.start()
        
        print("🎤 Streaming transcription started")
    
    def stop_streaming(self) -> str:
        """Stop streaming and return final transcription"""
        if not self._is_streaming:
            return ""
        
        self._is_streaming = False
        self._stop_event.set()
        
        # Stop audio stream
        if self._audio_stream:
            self._audio_stream.stop()
            self._audio_stream.close()
            self._audio_stream = None
        
        # Wait for processing thread
        if self._stream_thread:
            self._stream_thread.join(timeout=2.0)
            self._stream_thread = None
        
        # Get final transcription from all audio
        final_text = ""
        if self._audio_buffer:
            try:
                audio_data = np.concatenate(self._audio_buffer)
                if len(audio_data) > 0:
                    if audio_data.dtype != np.float32:
                        audio_data = audio_data.astype(np.float32)
                    
                    max_val = np.max(np.abs(audio_data))
                    if max_val > 0:
                        audio_data = audio_data / max_val
                    
                    segments = self._model.transcribe(
                        audio_data,
                        language=self.language
                    )
                    
                    final_text = " ".join([seg.text.strip() for seg in segments])
                    final_text = final_text.strip()
            except Exception as e:
                print(f"Final transcription error: {e}")
        
        self._audio_buffer = []
        print("⏹ Streaming transcription stopped")
        
        return final_text
    
    def transcribe(
        self,
        audio: np.ndarray,
        sample_rate: int = 16000
    ) -> Dict[str, Any]:
        """
        Transcribe audio (non-streaming, for compatibility with Transcriber API).
        
        Args:
            audio: Audio data as numpy array (float32, mono)
            sample_rate: Sample rate of the audio
        
        Returns:
            Dict with 'text', 'language', and 'segments'
        """
        if self._model is None:
            raise RuntimeError("Model not loaded")
        
        # Ensure float32
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)
        
        # Normalize
        max_val = np.max(np.abs(audio))
        if max_val > 0:
            audio = audio / max_val
        
        try:
            segments = self._model.transcribe(
                audio,
                language=self.language
            )
            
            text = " ".join([seg.text.strip() for seg in segments])
            text = text.strip()
            
            return {
                "text": text,
                "language": self.language or "auto",
                "segments": [{"text": seg.text, "start": seg.t0, "end": seg.t1} for seg in segments]
            }
        except Exception as e:
            print(f"Transcription error: {e}")
            return {"text": "", "language": self.language or "auto", "segments": []}
    
    def set_language(self, language: str) -> None:
        """Set the language for transcription"""
        self.language = language if language != "auto" else None


# Singleton instance
_streaming_transcriber: Optional[StreamingTranscriber] = None


def get_streaming_transcriber(
    model_name: str = StreamingTranscriber.DEFAULT_MODEL,
    language: str = "auto"
) -> StreamingTranscriber:
    """Get or create a singleton streaming transcriber instance"""
    global _streaming_transcriber
    if _streaming_transcriber is None:
        _streaming_transcriber = StreamingTranscriber(model_name, language)
    return _streaming_transcriber
