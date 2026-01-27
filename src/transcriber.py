"""
MWhisper Transcriber Module
Uses Parakeet-MLX for local speech-to-text on Apple Silicon
"""

import numpy as np
from typing import Optional, Dict, Any


class Transcriber:
    """Speech-to-text transcription using Parakeet-MLX"""
    
    def __init__(self, language: str = "auto"):
        """
        Initialize the transcriber with Parakeet-MLX model.
        
        Args:
            language: Language code or "auto" for auto-detection
        """
        self.language = language
        self.model = None
        self._load_model()
    
    def _load_model(self) -> None:
        """Load the Parakeet-MLX model"""
        try:
            from parakeet_mlx import from_pretrained
            # Load the Parakeet TDT v3 model from HuggingFace
            self.model = from_pretrained("mlx-community/parakeet-tdt-0.6b-v3")
            print("✓ Parakeet-MLX model loaded successfully")
        except ImportError as e:
            print(f"DEBUG: Failed to import parakeet_mlx: {e}")
            raise ImportError(
                f"parakeet-mlx import failed: {e}. Run: pip install parakeet-mlx"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to load Parakeet model: {e}")
    
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
        
        try:
            import tempfile
            import soundfile as sf
            
            # Parakeet-MLX expects a file path, not a numpy array
            # Save audio to temporary file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                temp_path = tmp_file.name
                # Write audio to temp file
                sf.write(temp_path, audio, sample_rate)
            
            try:
                # Ensure FFmpeg is in PATH for parakeet-mlx
                # In bundled app, ffmpeg is in Contents/Frameworks/
                import sys
                import os
                
                if getattr(sys, 'frozen', False):
                    # Running in PyInstaller bundle
                    bundle_dir = sys._MEIPASS
                    frameworks_dir = os.path.join(os.path.dirname(bundle_dir), 'Frameworks')
                    
                    # Add Frameworks directory to PATH
                    old_path = os.environ.get('PATH', '')
                    os.environ['PATH'] = frameworks_dir + os.pathsep + old_path
                
                # Transcribe using parakeet-mlx with file path
                # Returns AlignedResult with .text and .sentences attributes
                result = self.model.transcribe(temp_path)
                
                # Handle AlignedResult from parakeet-mlx
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
                # Clean up temp file
                import os
                try:
                    os.unlink(temp_path)
                except:
                    pass
                
                # CRITICAL: Clear MLX cache to prevent memory leak
                try:
                    import mlx.core as mx
                    mx.metal.clear_cache()
                except Exception as e:
                    pass  # Ignore if mlx.metal not available
                
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
