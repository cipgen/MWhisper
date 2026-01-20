
import sys
import os
import numpy as np

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

try:
    print("Attempting to import Transcriber...")
    from transcriber import Transcriber
    print("Import successful.")

    print("Initializing Transcriber (loading model)...")
    transcriber = Transcriber()
    print("Model loaded successfully.")

    print("Generating dummy audio (1 second silence)...")
    # Generate 1 second of silence at 16kHz
    audio = np.zeros(16000, dtype=np.float32)

    print("Attempting transcription...")
    result = transcriber.transcribe(audio)
    print("Transcription result:", result)

except Exception as e:
    print(f"\nCRITICAL ERROR: {e}")
    import traceback
    traceback.print_exc()
