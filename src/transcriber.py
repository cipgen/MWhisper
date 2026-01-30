"""
MWhisper Transcriber Module
Cross-platform speech-to-text transcription
Uses Parakeet-MLX on macOS, faster-whisper on Windows
"""

import numpy as np
from typing import Optional, Dict, Any
from .platform import is_macos, is_windows


class Transcriber:
    """Speech-to-text transcription - cross-platform"""
    
    def __init__(self, language: str = "auto"):
        """
        Initialize the transcriber with appropriate backend.
        
        Args:
            language: Language code or "auto" for auto-detection
        """
        self.language = language
        self.model = None
        self._backend = "parakeet" if is_macos() else "faster-whisper"
        self._load_model()
    
    def _load_model(self) -> None:
        """Load the transcription model"""
        if is_macos():
            self._load_parakeet()
        else:
            self._load_faster_whisper()
    
    def _load_parakeet(self) -> None:
        """Load Parakeet-MLX model (macOS only)"""
        try:
            from parakeet_mlx import from_pretrained
            self.model = from_pretrained("mlx-community/parakeet-tdt-0.6b-v3")
            print("✓ Parakeet-MLX model loaded successfully")
        except ImportError as e:
            raise ImportError(
                f"parakeet-mlx import failed: {e}. Run: pip install parakeet-mlx"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to load Parakeet model: {e}")
    
    def _load_faster_whisper(self) -> None:
        """Load faster-whisper model (Windows/Linux)"""
        try:
            from faster_whisper import WhisperModel
            
            # Use CUDA if available, else CPU
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
            compute_type = "float16" if device == "cuda" else "int8"
            
            print(f"Loading faster-whisper model on {device}...")
            self.model = WhisperModel(
                "medium", 
                device=device, 
                compute_type=compute_type
            )
            print(f"✓ faster-whisper model loaded successfully ({device})")
        except ImportError as e:
            raise ImportError(
                f"faster-whisper import failed: {e}. Run: pip install faster-whisper torch"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to load faster-whisper model: {e}")
    
    def transcribe(
        self,
        audio: np.ndarray,
        sample_rate: int = 16000
    ) -> Dict[str, Any]:
        """
        Transcribe audio to text.
        
        Args:
            audio: Audio data as numpy array (float32, mono)
            sample_rate: Sample rate of the audio (default 16000)
        
        Returns:
            Dict with 'text', 'language' (detected), and 'segments'
        """
        if self.model is None:
            raise RuntimeError("Model not loaded")
        
        # Ensure audio is float32 and normalized
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)
        
        # Normalize if needed
        if np.max(np.abs(audio)) > 1.0:
            audio = audio / np.max(np.abs(audio))
        
        if is_macos():
            return self._transcribe_parakeet(audio, sample_rate)
        else:
            return self._transcribe_faster_whisper(audio, sample_rate)
    
    def _transcribe_parakeet(self, audio: np.ndarray, sample_rate: int) -> Dict[str, Any]:
        """Transcribe using Parakeet-MLX"""
        try:
            import tempfile
            import soundfile as sf
            import os
            
            # Parakeet-MLX expects a file path
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                temp_path = tmp_file.name
                sf.write(temp_path, audio, sample_rate)
            
            try:
                import sys
                
                if getattr(sys, 'frozen', False):
                    bundle_dir = sys._MEIPASS
                    frameworks_dir = os.path.join(os.path.dirname(bundle_dir), 'Frameworks')
                    old_path = os.environ.get('PATH', '')
                    os.environ['PATH'] = frameworks_dir + os.pathsep + old_path
                
                result = self.model.transcribe(temp_path)
                
                if hasattr(result, 'text'):
                    text = result.text
                    segments = []
                    if hasattr(result, 'sentences'):
                        segments = [
                            {"text": s.text, "start": s.start, "end": s.end}
                            for s in result.sentences
                        ]
                    return {
                        "text": text,
                        "language": self.language if self.language != "auto" else "en",
                        "segments": segments
                    }
                elif isinstance(result, str):
                    return {
                        "text": result,
                        "language": self.language if self.language != "auto" else "en",
                        "segments": []
                    }
                else:
                    return {
                        "text": str(result),
                        "language": self.language,
                        "segments": []
                    }
            finally:
                try:
                    os.unlink(temp_path)
                except:
                    pass
                
                try:
                    import mlx.core as mx
                    mx.metal.clear_cache()
                except:
                    pass
                
        except Exception as e:
            print(f"Transcription error: {e}")
            import traceback
            traceback.print_exc()
            return {"text": "", "language": self.language, "segments": []}
    
    def _transcribe_faster_whisper(self, audio: np.ndarray, sample_rate: int) -> Dict[str, Any]:
        """Transcribe using faster-whisper"""
        try:
            language = self.language if self.language != "auto" else None
            
            segments, info = self.model.transcribe(
                audio,
                language=language,
                beam_size=5,
                vad_filter=True
            )
            
            segments_list = list(segments)
            text = " ".join([seg.text.strip() for seg in segments_list])
            
            return {
                "text": text.strip(),
                "language": info.language if hasattr(info, 'language') else (language or "en"),
                "segments": [
                    {"text": seg.text, "start": seg.start, "end": seg.end}
                    for seg in segments_list
                ]
            }
        except Exception as e:
            print(f"Transcription error: {e}")
            import traceback
            traceback.print_exc()
            return {"text": "", "language": self.language, "segments": []}
    
    def transcribe_file(self, filepath: str) -> Dict[str, Any]:
        """
        Transcribe audio from file.
        
        Args:
            filepath: Path to audio file
        
        Returns:
            Dict with 'text', 'language', and 'segments'
        """
        try:
            import soundfile as sf
            audio, sample_rate = sf.read(filepath)
            
            # Convert to mono if stereo
            if len(audio.shape) > 1:
                audio = np.mean(audio, axis=1)
            
            return self.transcribe(audio, sample_rate)
        except ImportError:
            raise ImportError("soundfile not installed. Run: pip install soundfile")
    
    def set_language(self, language: str) -> None:
        """Set the language for transcription"""
        self.language = language


# Singleton instance for reuse
_transcriber_instance: Optional[Transcriber] = None


def get_transcriber(language: str = "auto") -> Transcriber:
    """Get or create a singleton transcriber instance"""
    global _transcriber_instance
    if _transcriber_instance is None:
        _transcriber_instance = Transcriber(language)
    return _transcriber_instance
